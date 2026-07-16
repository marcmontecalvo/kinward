from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.assistants import AssistantNotFound, update_own_primary_assistant
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
    return person, assistant


async def test_owner_can_rename_their_own_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        person, _assistant = await _seed_owner_with_assistant(session)

        result = await update_own_primary_assistant(
            session, ha_user_id="ha-user-marc", name="Jarvis"
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.name == "Jarvis"
        assert result.owner_person_id == person.id


async def test_owner_can_set_personality_preferences() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_owner_with_assistant(session)

        result = await update_own_primary_assistant(
            session, ha_user_id="ha-user-marc", personality={"tone": "warm", "verbosity": "brief"}
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.personality == {"tone": "warm", "verbosity": "brief"}


async def test_preferences_never_touch_the_owning_person() -> None:
    factory = await _factory()
    async with factory() as session:
        person, _assistant = await _seed_owner_with_assistant(session)

        await update_own_primary_assistant(
            session, ha_user_id="ha-user-marc", name="Jarvis", personality={"tone": "warm"}
        )
        await session.commit()

        refreshed = await session.get(PersonRecord, person.id)
        assert refreshed is not None
        assert refreshed.role == "member"
        assert refreshed.profile_kind == "adult"


async def test_unmapped_ha_user_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        result = await update_own_primary_assistant(session, ha_user_id="unknown", name="Jarvis")
        assert isinstance(result, Unmapped)


async def test_person_without_a_primary_assistant_fails_closed() -> None:
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

        result = await update_own_primary_assistant(session, ha_user_id="ha-user-marc", name="Jarvis")
        assert isinstance(result, AssistantNotFound)
