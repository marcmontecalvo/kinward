from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.pets import (
    Deleted,
    PetNotFound,
    create_pet,
    delete_pet,
    list_pets,
    update_pet,
)
from kinward.persistence.models import Base, HouseholdRecord


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


async def test_create_and_list_pets() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)

        pet = await create_pet(
            session,
            household_id=household.id,
            display_name="Biscuit",
            species="Dog",
            shared_facts=["Needs a walk every morning"],
        )
        await session.commit()

        assert pet.household_id == household.id
        pets = await list_pets(session, household_id=household.id)
        assert [pet.display_name for pet in pets] == ["Biscuit"]


async def test_update_pet_changes_only_provided_fields() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        pet = await create_pet(
            session,
            household_id=household.id,
            display_name="Biscuit",
            species="Dog",
            shared_facts=[],
        )
        await session.commit()

        updated = await update_pet(
            session, household_id=household.id, pet_id=pet.id, species="Golden Retriever"
        )
        await session.commit()

        assert not isinstance(updated, PetNotFound)
        assert updated.display_name == "Biscuit"
        assert updated.species == "Golden Retriever"


async def test_update_unknown_pet_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        result = await update_pet(
            session, household_id=household.id, pet_id="does-not-exist", species="Cat"
        )
        assert isinstance(result, PetNotFound)


async def test_update_pet_scoped_to_the_wrong_household_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        pet = await create_pet(
            session, household_id=household.id, display_name="Biscuit", species="Dog", shared_facts=[]
        )
        await session.commit()

        result = await update_pet(
            session, household_id="not-this-household", pet_id=pet.id, species="Cat"
        )
        assert isinstance(result, PetNotFound)


async def test_delete_pet() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        pet = await create_pet(
            session, household_id=household.id, display_name="Biscuit", species="Dog", shared_facts=[]
        )
        await session.commit()

        result = await delete_pet(session, household_id=household.id, pet_id=pet.id)
        await session.commit()

        assert result == Deleted(pet_id=pet.id)
        assert await list_pets(session, household_id=household.id) == []


async def test_delete_unknown_pet_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        result = await delete_pet(session, household_id=household.id, pet_id="does-not-exist")
        assert isinstance(result, PetNotFound)
