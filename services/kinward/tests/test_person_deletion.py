from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.person_deletion import (
    AdminInvariantBlocked,
    Deleted,
    PersonNotFound,
    delete_person,
)
from kinward.persistence.models import Base, HouseholdRecord, PersonRecord


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


async def _add_person(session, household, *, role: str, ha_person_id: str):  # type: ignore[no-untyped-def]
    person = PersonRecord(
        household_id=household.id,
        display_name=ha_person_id,
        role=role,
        profile_kind="adult",
        ha_person_id=ha_person_id,
    )
    session.add(person)
    await session.flush()
    return person


async def test_deleting_a_non_admin_is_always_allowed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        admin = await _add_person(session, household, role="admin", ha_person_id="admin")
        member = await _add_person(session, household, role="member", ha_person_id="member")
        await session.commit()

        result = await delete_person(session, household_id=household.id, person_id=member.id)
        await session.commit()

        assert result == Deleted(person_id=member.id)
        assert await session.get(PersonRecord, admin.id) is not None


async def test_deleting_one_of_several_admins_is_allowed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        first_admin = await _add_person(session, household, role="admin", ha_person_id="first")
        second_admin = await _add_person(session, household, role="admin", ha_person_id="second")
        await session.commit()

        result = await delete_person(session, household_id=household.id, person_id=first_admin.id)
        await session.commit()

        assert result == Deleted(person_id=first_admin.id)
        assert await session.get(PersonRecord, second_admin.id) is not None


async def test_deleting_the_sole_admin_is_blocked() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        admin = await _add_person(session, household, role="admin", ha_person_id="admin")
        await session.commit()

        result = await delete_person(session, household_id=household.id, person_id=admin.id)

        assert isinstance(result, AdminInvariantBlocked)
        assert result.code == "household_requires_an_admin"
        assert await session.get(PersonRecord, admin.id) is not None


async def test_deleting_unknown_person_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        result = await delete_person(session, household_id=household.id, person_id="does-not-exist")
        assert isinstance(result, PersonNotFound)
