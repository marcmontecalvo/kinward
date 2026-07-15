from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.persistence.models import AssistantRecord, Base, HouseholdRecord, PersonRecord


async def test_single_household_schema_round_trip() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()

        person = PersonRecord(
            household_id=household.id,
            display_name="Example Adult",
            role="admin",
            email="adult@example.invalid",
        )
        session.add(person)
        await session.flush()

        assistant = AssistantRecord(
            household_id=household.id,
            owner_person_id=person.id,
            name="Atlas",
            kind="primary",
        )
        session.add(assistant)
        await session.commit()

    async with factory() as session:
        result = await session.execute(select(AssistantRecord))
        stored = result.scalar_one()
        assert stored.name == "Atlas"
        assert stored.kind == "primary"
        assert stored.owner_person_id is not None

    await engine.dispose()
