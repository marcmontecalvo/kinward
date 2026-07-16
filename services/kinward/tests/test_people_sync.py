from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.people_sync import SyncedPerson, sync_people
from kinward.persistence.models import ActivityRecord, AssistantRecord, Base, HouseholdRecord, PersonRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_household(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    return household


async def test_sync_creates_a_person_and_primary_assistant_atomically() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        synced = await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc")],
        )
        await session.commit()

        assert len(synced) == 1
        person = synced[0]
        assert person.role == "member"
        assert person.profile_kind == "adult"
        assert person.ha_person_id == "marc"
        assert person.ha_user_id == "ha-user-marc"

        assistant = await session.scalar(
            select(AssistantRecord).where(AssistantRecord.owner_person_id == person.id)
        )
        assert assistant is not None
        assert assistant.kind == "primary"


async def test_sync_represents_a_household_member_with_no_login() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        synced = await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="lisa", ha_user_id=None, display_name="Lisa")],
        )
        await session.commit()

        assert synced[0].ha_user_id is None
        assert synced[0].ha_person_id == "lisa"


async def test_a_rename_updates_display_name_without_touching_the_person_or_user_link() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        [first] = await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc")],
        )
        await session.commit()
        person_id = first.id

        [renamed] = await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marcus")],
        )
        await session.commit()

        assert renamed.id == person_id
        assert renamed.display_name == "Marcus"
        assert renamed.ha_person_id == "marc"
        assert renamed.ha_user_id == "ha-user-marc"

        assistants = (await session.scalars(select(AssistantRecord))).all()
        assert len(assistants) == 1, "a rename never creates a second person or assistant"


async def test_toggling_login_off_clears_ha_user_id_without_deleting_the_person() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc")],
        )
        await session.commit()

        [updated] = await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id=None, display_name="Marc")],
        )
        await session.commit()

        assert updated.ha_user_id is None
        assert await session.scalar(select(func.count()).select_from(PersonRecord)) == 1


async def test_a_person_missing_from_the_payload_is_left_disconnected_not_deleted() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        await sync_people(
            session,
            household_id=household.id,
            people=[SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc")],
        )
        await session.commit()

        await sync_people(session, household_id=household.id, people=[])
        await session.commit()

        remaining = await session.scalar(select(PersonRecord).where(PersonRecord.ha_person_id == "marc"))
        assert remaining is not None
        assert remaining.ha_user_id == "ha-user-marc"


async def test_sync_creates_an_ha_admin_as_a_kinward_admin() -> None:
    """Kinward has no admin designation of its own - being an HA admin is the whole rule."""
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        [person] = await sync_people(
            session,
            household_id=household.id,
            people=[
                SyncedPerson(
                    ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc", is_admin=True
                )
            ],
        )
        await session.commit()

        assert person.role == "admin"
        activity = await session.scalar(select(ActivityRecord))
        assert activity is not None and activity.detail["role"] == "admin"


async def test_sync_supports_more_than_one_simultaneous_admin() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        synced = await sync_people(
            session,
            household_id=household.id,
            people=[
                SyncedPerson(ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc", is_admin=True),
                SyncedPerson(ha_person_id="lisa", ha_user_id="ha-user-lisa", display_name="Lisa", is_admin=True),
                SyncedPerson(ha_person_id="kid", ha_user_id=None, display_name="Kid", is_admin=False),
            ],
        )
        await session.commit()

        roles = {person.ha_person_id: person.role for person in synced}
        assert roles == {"marc": "admin", "lisa": "admin", "kid": "member"}


async def test_a_later_sync_pass_reconciles_role_as_ha_admin_status_changes() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        await sync_people(
            session,
            household_id=household.id,
            people=[
                SyncedPerson(
                    ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc", is_admin=False
                )
            ],
        )
        await session.commit()

        [promoted] = await sync_people(
            session,
            household_id=household.id,
            people=[
                SyncedPerson(
                    ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc", is_admin=True
                )
            ],
        )
        await session.commit()
        assert promoted.role == "admin"

        [demoted] = await sync_people(
            session,
            household_id=household.id,
            people=[
                SyncedPerson(
                    ha_person_id="marc", ha_user_id="ha-user-marc", display_name="Marc", is_admin=False
                )
            ],
        )
        await session.commit()
        assert demoted.role == "member"

        role_change_count = await session.scalar(
            select(func.count())
            .select_from(ActivityRecord)
            .where(ActivityRecord.summary == "Household role changed to match Home Assistant admin status")
        )
        assert role_change_count == 2, "both the promotion and the demotion are recorded"
        assert await session.scalar(select(func.count()).select_from(PersonRecord)) == 1
