from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from kinward.application.calendar import (
    SyncSummary,
    list_items_needing_notification,
    mark_attention_item_notified,
    sync_household_calendars,
)
from kinward.application.household_summary import fetch_household_summary
from kinward.application.knowledge import expire_due_observations
from kinward.application.provider_settings import get_or_create_provider_settings
from kinward.config import Settings, get_settings
from kinward.domain.expected_state import expected_state_for
from kinward.health import CORE_WORKER_NAME, EXPECTED_SCHEMA_REVISION
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.memory.factory import knowledge_store_provider
from kinward.persistence.models import ActivityRecord, OutboxMessageRecord, WorkerHeartbeatRecord

# Story 7.3: "ambiguous or missing observations preserve unknown state until
# reconciliation." Past this age, a confirmation is unlikely to ever land (the HA
# session that submitted it is long gone) - the row resolves to "failed" instead of
# staying "unknown" forever, matching the ApprovalRecord fail-closed precedent for
# every other unconfirmable case.
RECONCILIATION_GIVE_UP_AFTER = timedelta(hours=1)


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


def _aware(value: datetime) -> datetime:
    """SQLite round-trips ``DateTime(timezone=True)`` values as naive - same normalization
    ``application/pending_actions.py`` applies before comparing against an aware ``datetime``.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def reconcile_unknown_activity(
    factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    ha_client: HomeAssistantClient | None = None,
    now: datetime | None = None,
) -> int:
    """Resolve ``ActivityRecord`` rows left at outcome ``"unknown"`` by Story 7.3's
    expected-state confirmation (``application/pending_actions._submit_and_confirm``) -
    "ambiguous or missing observations preserve unknown state until reconciliation."

    Every such row's ``detail`` carries the original ``domain``/``service``/``entity_id`` -
    a fresh ``get_state`` read that now matches the service's expected end state
    (``domain/expected_state.py``) resolves the row to ``"completed"``; one still unconfirmed
    past ``RECONCILIATION_GIVE_UP_AFTER`` resolves to ``"failed"`` instead of retrying forever.
    A row for a service with no deterministic expected state (nothing to confirm against) is
    left untouched. One deployment serves one household, so a single HA client covers every
    row in a pass.
    """
    resolved_at = now or datetime.now(UTC)
    async with factory() as session:
        rows = list(
            await session.scalars(select(ActivityRecord).where(ActivityRecord.outcome == "unknown"))
        )
        if not rows:
            return 0
        resolved_ha_client = ha_client or HomeAssistantClient(
            base_url=settings.home_assistant_url, token=settings.home_assistant_token
        )
        resolved_count = 0
        for activity in rows:
            detail = activity.detail if isinstance(activity.detail, dict) else {}
            domain = detail.get("domain")
            service = detail.get("service")
            entity_id = detail.get("entity_id")
            if not isinstance(domain, str) or not isinstance(service, str) or not isinstance(
                entity_id, str
            ):
                continue
            expected_state = expected_state_for(domain=domain, service=service)
            if expected_state is None:
                continue

            if resolved_at - _aware(activity.occurred_at) > RECONCILIATION_GIVE_UP_AFTER:
                activity.outcome = "failed"
                activity.detail = {**detail, "reconciliation": "gave_up"}
                resolved_count += 1
                continue

            observed = await resolved_ha_client.get_state(entity_id)
            observed_state = observed.get("state") if observed else None
            if observed_state == expected_state:
                activity.outcome = "completed"
                activity.detail = {
                    **detail,
                    "observed_state": observed_state,
                    "reconciliation": "confirmed",
                }
                resolved_count += 1
        await session.commit()
        return resolved_count


async def sync_calendars(
    factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    ha_client: HomeAssistantClient | None = None,
    now: datetime | None = None,
) -> SyncSummary | None:
    """Fetch enabled HA calendar entities and detect/track meaningful changes (Epic 5
    Story 5.2/5.3). One deployment serves one household, so there's at most one
    household's calendars to sync each pass - "Kinward responds to Home Assistant
    calendar updates without requiring its own dashboard polling schedule" refers to
    the HA dashboard card, not this backend sync, which still has to poll HA itself
    since HA gives Kinward no calendar-change webhook/push today.
    """
    async with factory() as session:
        summary = await fetch_household_summary(session)
        if summary is None:
            return None
        resolved_ha_client = ha_client or HomeAssistantClient(
            base_url=settings.home_assistant_url, token=settings.home_assistant_token
        )
        result = await sync_household_calendars(
            session, household_id=summary.id, ha_client=resolved_ha_client, settings=settings, now=now
        )
        await session.commit()
        return result


async def deliver_attention_notifications(
    factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    ha_client: HomeAssistantClient | None = None,
    now: datetime | None = None,
) -> int:
    """Push a deduplicated Home Assistant notification for each newly-active or
    materially-changed attention item (Epic 5 Story 5.6). Delivery is best-effort and
    never gates the attention item's own truth/lifecycle state - a failed
    ``persistent_notification.create`` call simply leaves the item eligible to be
    retried next pass rather than marking anything as delivered. There is no
    household quiet-hours setting yet (v0 scope: no existing quiet-period
    infrastructure to hook into), so delivery is not yet time-of-day gated beyond the
    dedup/freshness rules already enforced by ``list_items_needing_notification``.
    """
    delivered_at = now or datetime.now(UTC)
    async with factory() as session:
        summary = await fetch_household_summary(session)
        if summary is None:
            return 0
        resolved_ha_client = ha_client or HomeAssistantClient(
            base_url=settings.home_assistant_url, token=settings.home_assistant_token
        )
        items = await list_items_needing_notification(session, household_id=summary.id)
        delivered = 0
        for item in items:
            result = await resolved_ha_client.call_service(
                domain="persistent_notification",
                service="create",
                data={
                    "notification_id": f"kinward-attention-{item.id}",
                    "title": "Kinward calendar update",
                    "message": item.summary,
                },
            )
            if result is not None:
                await mark_attention_item_notified(
                    session, item_id=item.id, record_version=item.record_version, now=delivered_at
                )
                delivered += 1
        await session.commit()
        return delivered


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
            try:
                await reconcile_unknown_activity(factory, settings=settings)
            except SQLAlchemyError:
                pass
            try:
                await sync_calendars(factory, settings=settings)
            except SQLAlchemyError:
                pass
            try:
                await deliver_attention_notifications(factory, settings=settings)
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
