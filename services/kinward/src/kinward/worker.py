from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from kinward.application.household_summary import fetch_household_summary
from kinward.application.knowledge import expire_due_observations
from kinward.application.provider_settings import get_or_create_provider_settings
from kinward.config import Settings, get_settings
from kinward.health import CORE_WORKER_NAME, EXPECTED_SCHEMA_REVISION
from kinward.memory.factory import knowledge_store_provider
from kinward.persistence.models import OutboxMessageRecord, WorkerHeartbeatRecord


class WorkerNotReadyError(RuntimeError):
    pass


async def schema_is_compatible(factory: async_sessionmaker[AsyncSession]) -> bool:
    try:
        async with factory() as session:
            revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
            return isinstance(revision, str) and revision == EXPECTED_SCHEMA_REVISION
    except (OSError, SQLAlchemyError):
        return False


async def record_heartbeat(
    factory: async_sessionmaker[AsyncSession],
    *,
    heartbeat_at: datetime | None = None,
) -> None:
    async with factory() as session:
        heartbeat = await session.get(WorkerHeartbeatRecord, CORE_WORKER_NAME)
        timestamp = heartbeat_at or datetime.now(UTC)
        if heartbeat is None:
            session.add(
                WorkerHeartbeatRecord(worker_name=CORE_WORKER_NAME, heartbeat_at=timestamp)
            )
        else:
            heartbeat.heartbeat_at = timestamp
        await session.commit()


async def check_readiness(settings: Settings) -> bool:
    engine: AsyncEngine | None = None
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        if not await schema_is_compatible(factory):
            return False
        async with factory() as session:
            await session.execute(select(OutboxMessageRecord.id).limit(1))
            heartbeat = await session.get(WorkerHeartbeatRecord, CORE_WORKER_NAME)
            if heartbeat is None:
                return False
            timestamp = heartbeat.heartbeat_at
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            return timestamp >= datetime.now(UTC) - timedelta(
                seconds=settings.worker_stale_after_seconds
            )
    except (OSError, SQLAlchemyError):
        return False
    finally:
        if engine is not None:
            await engine.dispose()


async def expire_pending_observations(factory: async_sessionmaker[AsyncSession]) -> int:
    """Dispose every pending inferred observation past its fixed 30-day expiry (AD-25).

    One deployment serves one household, so there's at most one household's
    provider settings to resolve each pass.
    """
    async with factory() as session:
        summary = await fetch_household_summary(session)
        if summary is None:
            return 0
        provider_settings = await get_or_create_provider_settings(session, household_id=summary.id)
        provider = knowledge_store_provider(
            backend=provider_settings.knowledge_backend, url=provider_settings.llm_wiki_url
        )
        count = await expire_due_observations(session, provider)
        await session.commit()
        return count


async def run_worker(settings: Settings) -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    if not await schema_is_compatible(factory):
        await engine.dispose()
        raise WorkerNotReadyError
    print("kinward-worker started", flush=True)
    try:
        while True:
            await record_heartbeat(factory)
            try:
                await expire_pending_observations(factory)
            except SQLAlchemyError:
                pass
            await asyncio.sleep(settings.worker_heartbeat_interval_seconds)
    finally:
        await engine.dispose()
        print("kinward-worker stopped", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Kinward durable worker readiness process")
    parser.add_argument("--check", action="store_true", help="check durable worker readiness")
    args = parser.parse_args()
    settings = get_settings()
    if args.check:
        return 0 if asyncio.run(check_readiness(settings)) else 1
    try:
        asyncio.run(run_worker(settings))
    except (OSError, SQLAlchemyError, WorkerNotReadyError):
        print("kinward-worker schema is not ready", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
