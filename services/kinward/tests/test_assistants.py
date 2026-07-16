from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.assistant_policy import update_assistant_policy
from kinward.application.assistants import (
    AssistantNotFound,
    Deleted,
    InvalidAccessMode,
    PolicyBlocked,
    create_additional_assistant,
    delete_own_assistant,
    list_accessible_assistants,
    list_own_assistants,
    update_own_assistant,
)
from kinward.application.conversation import Unmapped
from kinward.persistence.models import AssistantRecord, Base, HouseholdRecord, PersonRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_owner_with_assistant(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Marc",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-marc",
        ha_user_id="ha-user-marc",
    )
    session.add(person)
    await session.flush()
    assistant = AssistantRecord(
        household_id=household.id,
        owner_person_id=person.id,
        name="Marc's Assistant",
        kind="primary",
    )
    session.add(assistant)
    await session.flush()
    return household, person, assistant


async def test_owner_can_rename_their_own_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person, assistant = await _seed_owner_with_assistant(session)

        result = await update_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id=assistant.id, name="Jarvis"
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.name == "Jarvis"
        assert result.owner_person_id == person.id


async def test_owner_can_set_personality_preferences() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, _person, assistant = await _seed_owner_with_assistant(session)

        result = await update_own_assistant(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            personality={"tone": "warm", "verbosity": "brief"},
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.personality == {"tone": "warm", "verbosity": "brief"}


async def test_preferences_never_touch_the_owning_person() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person, assistant = await _seed_owner_with_assistant(session)

        await update_own_assistant(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            name="Jarvis",
            personality={"tone": "warm"},
        )
        await session.commit()

        refreshed = await session.get(PersonRecord, person.id)
        assert refreshed is not None
        assert refreshed.role == "member"
        assert refreshed.profile_kind == "adult"


async def test_unmapped_ha_user_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        result = await update_own_assistant(
            session, ha_user_id="unknown", assistant_id="does-not-exist", name="Jarvis"
        )
        assert isinstance(result, Unmapped)


async def test_unknown_assistant_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, _person, _assistant = await _seed_owner_with_assistant(session)
        result = await update_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id="does-not-exist", name="Jarvis"
        )
        assert isinstance(result, AssistantNotFound)


async def test_cannot_update_another_persons_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person, assistant = await _seed_owner_with_assistant(session)
        other = PersonRecord(
            household_id=household.id,
            display_name="Lisa",
            role="member",
            profile_kind="adult",
            ha_person_id="ha-person-lisa",
            ha_user_id="ha-user-lisa",
        )
        session.add(other)
        await session.flush()

        result = await update_own_assistant(
            session, ha_user_id="ha-user-lisa", assistant_id=assistant.id, name="Not yours"
        )
        assert isinstance(result, AssistantNotFound)


async def test_list_own_assistants_returns_only_the_resolved_persons_assistants() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person, assistant = await _seed_owner_with_assistant(session)
        other = PersonRecord(
            household_id=household.id,
            display_name="Lisa",
            role="member",
            profile_kind="adult",
            ha_person_id="ha-person-lisa",
            ha_user_id="ha-user-lisa",
        )
        session.add(other)
        await session.flush()
        session.add(
            AssistantRecord(
                household_id=household.id, owner_person_id=other.id, name="Lisa's Assistant", kind="primary"
            )
        )
        await session.commit()

        result = await list_own_assistants(session, ha_user_id="ha-user-marc")
        assert not isinstance(result, Unmapped)
        assert [a.id for a in result] == [assistant.id]
        _ = person


async def test_create_additional_assistant_with_no_policy_configured() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person, _assistant = await _seed_owner_with_assistant(session)

        result = await create_additional_assistant(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            name="Business Assistant",
            requester_is_admin=False,
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, PolicyBlocked))
        assert result.name == "Business Assistant"

        listed = await list_own_assistants(session, ha_user_id="ha-user-marc")
        assert not isinstance(listed, Unmapped)
        assert len(listed) == 2


async def test_max_assistants_per_person_is_enforced() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person, _assistant = await _seed_owner_with_assistant(session)
        await update_assistant_policy(session, household_id=household.id, max_assistants_per_person=1)
        await session.commit()

        result = await create_additional_assistant(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            name="Should not be created",
            requester_is_admin=False,
        )

        assert isinstance(result, PolicyBlocked)
        assert result.code == "max_assistants_reached"


async def test_admin_approval_gate_blocks_a_non_admin_and_allows_an_admin() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person, _assistant = await _seed_owner_with_assistant(session)
        await update_assistant_policy(
            session, household_id=household.id, require_admin_approval_for_creation=True
        )
        await session.commit()

        blocked = await create_additional_assistant(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            name="Specialist",
            requester_is_admin=False,
        )
        assert isinstance(blocked, PolicyBlocked)
        assert blocked.code == "admin_approval_required"

        allowed = await create_additional_assistant(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            name="Specialist",
            requester_is_admin=True,
        )
        assert not isinstance(allowed, (Unmapped, PolicyBlocked))


async def test_can_delete_one_of_several_assistants() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person, assistant = await _seed_owner_with_assistant(session)
        second = await create_additional_assistant(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            name="Second Assistant",
            requester_is_admin=False,
        )
        await session.commit()
        assert not isinstance(second, (Unmapped, PolicyBlocked))

        result = await delete_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id=second.id
        )
        await session.commit()

        assert result == Deleted(assistant_id=second.id)
        remaining = await list_own_assistants(session, ha_user_id="ha-user-marc")
        assert not isinstance(remaining, Unmapped)
        assert [a.id for a in remaining] == [assistant.id]


async def test_cannot_delete_a_persons_last_remaining_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, _person, assistant = await _seed_owner_with_assistant(session)

        result = await delete_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id=assistant.id
        )

        assert isinstance(result, PolicyBlocked)
        assert result.code == "last_assistant"


async def test_person_without_any_assistant_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        person = PersonRecord(
            household_id=household.id,
            display_name="Marc",
            role="member",
            profile_kind="adult",
            ha_person_id="ha-person-marc",
            ha_user_id="ha-user-marc",
        )
        session.add(person)
        await session.flush()

        result = await update_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id="does-not-exist", name="Jarvis"
        )
        assert isinstance(result, AssistantNotFound)


async def _seed_two_people(session):  # type: ignore[no-untyped-def]
    household, marc, bob = await _seed_owner_with_assistant(session)
    lisa = PersonRecord(
        household_id=household.id,
        display_name="Lisa",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-lisa",
        ha_user_id="ha-user-lisa",
    )
    session.add(lisa)
    await session.flush()
    return household, marc, bob, lisa


async def test_owner_can_set_access_mode_and_allowlist() -> None:
    """``allowed_person_ids`` holds internal PersonRecord ids, like every other

    cross-reference in this codebase (owner_person_id, requested_by_person_id, ...)
    - never ha_person_id, which is a different identifier space entirely.
    """
    factory = await _factory()
    async with factory() as session:
        _household, _marc, bob, lisa = await _seed_two_people(session)

        result = await update_own_assistant(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=bob.id,
            access_mode="allowlist",
            allowed_person_ids=[lisa.id],
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound, InvalidAccessMode))
        assert result.access_mode == "allowlist"
        assert result.allowed_person_ids == [lisa.id]


async def test_invalid_access_mode_is_rejected() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, _marc, bob, _lisa = await _seed_two_people(session)

        result = await update_own_assistant(
            session, ha_user_id="ha-user-marc", assistant_id=bob.id, access_mode="anyone-with-a-key"
        )

        assert isinstance(result, InvalidAccessMode)


async def test_list_accessible_assistants_owner_only_excludes_non_owner() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _marc, bob, _lisa = await _seed_two_people(session)
        await session.commit()

        result = await list_accessible_assistants(
            session, household_id=household.id, ha_user_id="ha-user-lisa"
        )
        assert not isinstance(result, Unmapped)
        assert bob.id not in [a.id for a in result]


async def test_list_accessible_assistants_household_mode_includes_non_owner() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _marc, bob, _lisa = await _seed_two_people(session)
        bob.access_mode = "household"
        await session.commit()

        result = await list_accessible_assistants(
            session, household_id=household.id, ha_user_id="ha-user-lisa"
        )
        assert not isinstance(result, Unmapped)
        assert bob.id in [a.id for a in result]


async def test_list_accessible_assistants_allowlist_mode_is_selective() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _marc, bob, lisa = await _seed_two_people(session)
        bob.access_mode = "allowlist"
        bob.allowed_person_ids = [lisa.id]
        await session.commit()

        accessible_to_lisa = await list_accessible_assistants(
            session, household_id=household.id, ha_user_id="ha-user-lisa"
        )
        assert not isinstance(accessible_to_lisa, Unmapped)
        assert bob.id in [a.id for a in accessible_to_lisa]

        third = PersonRecord(
            household_id=household.id,
            display_name="Nia",
            role="member",
            profile_kind="adult",
            ha_person_id="ha-person-nia",
            ha_user_id="ha-user-nia",
        )
        session.add(third)
        await session.commit()

        accessible_to_nia = await list_accessible_assistants(
            session, household_id=household.id, ha_user_id="ha-user-nia"
        )
        assert not isinstance(accessible_to_nia, Unmapped)
        assert bob.id not in [a.id for a in accessible_to_nia]
