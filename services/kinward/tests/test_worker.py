from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.config import Settings
from kinward.persistence.models import (
    Base,
    HouseholdRecord,
    KnowledgeFactRecord,
    PersonRecord,
    WorkerHeartbeatRecord,
)
from kinward.worker import check_readiness, expire_pending_observations, record_heartbeat


async def test_worker_heartbeat_is_durable_and_idempotent(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    first = datetime.now(UTC)
    second = datetime.now(UTC)
    await record_heartbeat(factory, heartbeat_at=first)
    await record_heartbeat(factory, heartbeat_at=second)

    async with factory() as session:
        heartbeats = (await session.scalars(select(WorkerHeartbeatRecord))).all()
    assert len(heartbeats) == 1
    stored = heartbeats[0].heartbeat_at
    if stored.tzinfo is None:
        stored = stored.replace(tzinfo=UTC)
    assert stored == second
    await engine.dispose()


async def test_worker_readiness_rejects_a_database_without_migration_state(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "unmigrated.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    assert not await check_readiness(
        Settings(_env_file=None, database_url=f"sqlite+aiosqlite:///{database_path}")
    )


async def test_expire_pending_observations_reports_zero_without_a_household() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    assert await expire_pending_observations(factory) == 0
    await engine.dispose()


async def test_expire_pending_observations_disposes_facts_past_their_fixed_expiry() -> None:
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
            profile_kind="adult",
            ha_person_id="ha-person-1",
        )
        session.add(person)
        await session.flush()
        session.add(
            KnowledgeFactRecord(
                household_id=household.id,
                owner_person_id=person.id,
                subject="Example Adult",
                predicate="likes",
                value="tea",
                privacy="personal",
                source_system="conversation-inference",
                recurrence_key="worker-test-key",
                knowledge_state="pending",
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
        )
        await session.commit()

    count = await expire_pending_observations(factory)
    assert count == 1

    async with factory() as session:
        record = await session.scalar(select(KnowledgeFactRecord))
        assert record is not None
        assert record.knowledge_state == "expired"
    await engine.dispose()
