from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.resource_labels import (
    delete_resource_label,
    get_resource_label_overrides,
    list_resource_labels,
    set_resource_label,
)
from kinward.persistence.models import Base, HouseholdRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _household(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    return household


async def test_set_resource_label_creates_a_new_override() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _household(session)
        record = await set_resource_label(
            session, household_id=household.id, entity_id="light.office", label="Office Light"
        )
        await session.commit()
        assert record.entity_id == "light.office"
        assert record.label == "Office Light"
        assert record.record_version == 1


async def test_set_resource_label_updates_an_existing_override_and_bumps_the_version() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _household(session)
        await set_resource_label(
            session, household_id=household.id, entity_id="light.office", label="Office Light"
        )
        updated = await set_resource_label(
            session, household_id=household.id, entity_id="light.office", label="Study Light"
        )
        await session.commit()
        assert updated.label == "Study Light"
        assert updated.record_version == 2

        labels = await list_resource_labels(session, household_id=household.id)
        assert len(labels) == 1


async def test_get_resource_label_overrides_returns_an_entity_id_keyed_dict() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _household(session)
        await set_resource_label(
            session, household_id=household.id, entity_id="light.office", label="Office Light"
        )
        await set_resource_label(
            session, household_id=household.id, entity_id="lock.front_door", label="Front Door"
        )
        await session.commit()

        overrides = await get_resource_label_overrides(session, household_id=household.id)
        assert overrides == {"light.office": "Office Light", "lock.front_door": "Front Door"}


async def test_delete_resource_label_removes_an_existing_override() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _household(session)
        await set_resource_label(
            session, household_id=household.id, entity_id="light.office", label="Office Light"
        )
        await session.commit()

        deleted = await delete_resource_label(
            session, household_id=household.id, entity_id="light.office"
        )
        await session.commit()
        assert deleted is True

        overrides = await get_resource_label_overrides(session, household_id=household.id)
        assert overrides == {}


async def test_delete_resource_label_is_a_no_op_for_a_missing_override() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _household(session)
        deleted = await delete_resource_label(
            session, household_id=household.id, entity_id="light.office"
        )
        await session.commit()
        assert deleted is False
