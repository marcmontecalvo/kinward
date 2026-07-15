from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.persistence.models import Base, WorkerHeartbeatRecord
from kinward.worker import check_readiness, record_heartbeat
from kinward.config import Settings


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
