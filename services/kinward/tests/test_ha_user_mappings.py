from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.ha_user_mappings import (
    MappingError,
    list_mappings,
    remove_mapping,
    resolve_mapping,
    upsert_mapping,
)
from kinward.persistence.models import AccountRecord, ActivityRecord, Base, HouseholdRecord, PersonRecord


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


async def _add_account_bearing_person(session, household, *, email: str = "adult@example.invalid"):  # type: ignore[no-untyped-def]
    person = PersonRecord(
        household_id=household.id, display_name="Example Adult", role="admin", profile_kind="adult"
    )
    session.add(person)
    await session.flush()
    session.add(
        AccountRecord(household_id=household.id, person_id=person.id, email=email, password_verifier="x")
    )
    await session.flush()
    return person


async def _seed_account_bearing_person(session, *, email: str = "adult@example.invalid"):  # type: ignore[no-untyped-def]
    household = await _seed_household(session)
    person = await _add_account_bearing_person(session, household, email=email)
    return household, person


async def test_upsert_creates_and_updates_a_mapping() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person = await _seed_account_bearing_person(session)

        record = await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
        await session.commit()
        assert record.person_id == person.id

        again = await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
        await session.commit()
        assert again.id == record.id
        assert again.record_version == 2

        activity_count = await session.scalar(select(func.count()).select_from(ActivityRecord))
        assert activity_count == 2


async def test_upsert_rejects_a_person_without_an_account() -> None:
    factory = await _factory()
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        child = PersonRecord(
            household_id=household.id, display_name="Example Child", role="member", profile_kind="child"
        )
        session.add(child)
        await session.flush()

        try:
            await upsert_mapping(session, ha_user_id="ha-user-1", person_id=child.id)
            assert False, "expected MappingError"
        except MappingError as error:
            assert error.code == "person_not_account_bearing"


async def test_upsert_rejects_an_unknown_person() -> None:
    factory = await _factory()
    async with factory() as session:
        try:
            await upsert_mapping(session, ha_user_id="ha-user-1", person_id="does-not-exist")
            assert False, "expected MappingError"
        except MappingError as error:
            assert error.code == "person_not_found"


async def test_resolve_fails_closed_for_a_missing_mapping() -> None:
    factory = await _factory()
    async with factory() as session:
        assert await resolve_mapping(session, ha_user_id="unmapped-ha-user") is None


async def test_resolve_fails_closed_when_the_mapped_person_has_no_account() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_account_bearing_person(session)
        await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
        await session.commit()

        account = await session.scalar(select(AccountRecord).where(AccountRecord.person_id == person.id))
        await session.delete(account)
        await session.commit()

        assert await resolve_mapping(session, ha_user_id="ha-user-1") is None


async def test_resolve_succeeds_for_a_valid_mapping() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person = await _seed_account_bearing_person(session)
        await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
        await session.commit()

        assert await resolve_mapping(session, ha_user_id="ha-user-1") == person.id


async def test_remove_mapping_is_idempotent_and_deletes_the_row() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person = await _seed_account_bearing_person(session)
        await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
        await session.commit()

        assert await remove_mapping(session, ha_user_id="ha-user-1") is True
        await session.commit()
        assert await remove_mapping(session, ha_user_id="ha-user-1") is False
        assert await resolve_mapping(session, ha_user_id="ha-user-1") is None


async def test_list_mappings_reports_all_rows() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        person_one = await _add_account_bearing_person(session, household, email="one@example.invalid")
        person_two = await _add_account_bearing_person(session, household, email="two@example.invalid")
        await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person_one.id)
        await upsert_mapping(session, ha_user_id="ha-user-2", person_id=person_two.id)
        await session.commit()

        records = await list_mappings(session)
        assert {record.ha_user_id for record in records} == {"ha-user-1", "ha-user-2"}
