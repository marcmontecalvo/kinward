from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.people import PersonNotFound, reclassify_person
from kinward.persistence.models import Base, HouseholdRecord, PersonRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_person(session, *, profile_kind: str = "adult"):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Kid",
        role="member",
        profile_kind=profile_kind,
        ha_person_id="ha-person-kid",
    )
    session.add(person)
    await session.flush()
    return household, person


async def test_reclassify_to_teen_updates_profile_kind_and_keeps_private_person_classification() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session, profile_kind="child")

        result = await reclassify_person(
            session, household_id=household.id, person_id=person.id, profile_kind="teen"
        )
        await session.commit()

        assert not isinstance(result, PersonNotFound)
        assert result.profile_kind == "teen"
        assert result.classification == "private-person"


async def test_reclassify_to_child_switches_classification_to_private_child() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session, profile_kind="adult")

        result = await reclassify_person(
            session, household_id=household.id, person_id=person.id, profile_kind="child"
        )
        await session.commit()

        assert not isinstance(result, PersonNotFound)
        assert result.profile_kind == "child"
        assert result.classification == "private-child"


async def test_reclassify_never_touches_role() -> None:
    factory = await _factory()
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        admin = PersonRecord(
            household_id=household.id,
            display_name="Admin",
            role="admin",
            profile_kind="adult",
            ha_person_id="ha-person-admin",
        )
        session.add(admin)
        await session.flush()

        result = await reclassify_person(
            session, household_id=household.id, person_id=admin.id, profile_kind="teen"
        )
        await session.commit()

        assert not isinstance(result, PersonNotFound)
        assert result.role == "admin"
        assert result.profile_kind == "teen"


async def test_reclassify_unknown_person_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()

        result = await reclassify_person(
            session, household_id=household.id, person_id="does-not-exist", profile_kind="teen"
        )
        assert isinstance(result, PersonNotFound)


async def test_reclassify_scoped_to_the_wrong_household_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)

        result = await reclassify_person(
            session, household_id="not-this-household", person_id=person.id, profile_kind="teen"
        )
        assert isinstance(result, PersonNotFound)
