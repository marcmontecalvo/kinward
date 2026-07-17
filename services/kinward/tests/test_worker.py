from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.config import Settings
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.persistence.models import (
    ActivityRecord,
    AttentionItemRecord,
    Base,
    HouseholdRecord,
    KnowledgeFactRecord,
    PersonRecord,
    WorkerHeartbeatRecord,
)
from kinward.worker import (
    RECONCILIATION_GIVE_UP_AFTER,
    check_readiness,
    deliver_attention_notifications,
    expire_pending_observations,
    reconcile_unknown_activity,
    record_heartbeat,
    sync_calendars,
)


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


async def _seeded_household(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    return household


def _reconciliation_ha_client(*, response_state: str | None) -> HomeAssistantClient:
    def handler(_request: httpx.Request) -> httpx.Response:
        if response_state is None:
            return httpx.Response(404)
        return httpx.Response(200, json={"entity_id": "light.office", "state": response_state})

    return HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )


async def test_reconcile_unknown_activity_confirms_a_matching_fresh_observation() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        session.add(
            ActivityRecord(
                household_id=household.id,
                summary="light.turn_off on light.office",
                outcome="unknown",
                detail={"domain": "light", "service": "turn_off", "entity_id": "light.office"},
                occurred_at=datetime.now(UTC),
            )
        )
        await session.commit()

    resolved = await reconcile_unknown_activity(
        factory, settings=Settings(_env_file=None), ha_client=_reconciliation_ha_client(response_state="off")
    )
    assert resolved == 1

    async with factory() as session:
        activity = await session.scalar(select(ActivityRecord))
        assert activity is not None
        assert activity.outcome == "completed"
        assert activity.detail["reconciliation"] == "confirmed"
    await engine.dispose()


async def test_reconcile_unknown_activity_leaves_a_still_mismatched_row_unknown_within_the_window() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        session.add(
            ActivityRecord(
                household_id=household.id,
                summary="light.turn_off on light.office",
                outcome="unknown",
                detail={"domain": "light", "service": "turn_off", "entity_id": "light.office"},
                occurred_at=datetime.now(UTC),
            )
        )
        await session.commit()

    resolved = await reconcile_unknown_activity(
        factory, settings=Settings(_env_file=None), ha_client=_reconciliation_ha_client(response_state="on")
    )
    assert resolved == 0

    async with factory() as session:
        activity = await session.scalar(select(ActivityRecord))
        assert activity is not None
        assert activity.outcome == "unknown"
    await engine.dispose()


async def test_reconcile_unknown_activity_gives_up_past_the_reconciliation_window() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    stale_occurred_at = datetime.now(UTC) - RECONCILIATION_GIVE_UP_AFTER - timedelta(minutes=1)
    async with factory() as session:
        household = await _seeded_household(session)
        session.add(
            ActivityRecord(
                household_id=household.id,
                summary="light.turn_off on light.office",
                outcome="unknown",
                detail={"domain": "light", "service": "turn_off", "entity_id": "light.office"},
                occurred_at=stale_occurred_at,
            )
        )
        await session.commit()

    resolved = await reconcile_unknown_activity(
        factory, settings=Settings(_env_file=None), ha_client=_reconciliation_ha_client(response_state="on")
    )
    assert resolved == 1

    async with factory() as session:
        activity = await session.scalar(select(ActivityRecord))
        assert activity is not None
        assert activity.outcome == "failed"
        assert activity.detail["reconciliation"] == "gave_up"
    await engine.dispose()


async def test_sync_calendars_reports_none_without_a_household() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    result = await sync_calendars(factory, settings=Settings(_env_file=None))
    assert result is None
    await engine.dispose()


async def test_sync_calendars_reports_zero_entities_when_none_are_enabled() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        await _seeded_household(session)
        await session.commit()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )
    result = await sync_calendars(factory, settings=Settings(_env_file=None), ha_client=client)
    assert result is not None
    assert result.entities_synced == 0
    await engine.dispose()


def _notification_ha_client(*, accept: bool) -> HomeAssistantClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/services/persistent_notification/create":
            return httpx.Response(200, json=[]) if accept else httpx.Response(500)
        return httpx.Response(404)

    return HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )


async def test_deliver_attention_notifications_marks_delivered_items_notified() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        item = AttentionItemRecord(
            household_id=household.id,
            entity_id="calendar.family",
            event_uid="e1",
            change_type="cancelled",
            recurrence_key="key-1",
            state="active",
            summary="Cancelled: Dentist",
            detail={},
        )
        session.add(item)
        await session.commit()
        item_id = item.id

    delivered = await deliver_attention_notifications(
        factory, settings=Settings(_env_file=None), ha_client=_notification_ha_client(accept=True)
    )
    assert delivered == 1

    async with factory() as session:
        item = await session.get(AttentionItemRecord, item_id)
        assert item is not None
        assert item.notified_record_version == item.record_version
        assert item.last_notified_at is not None


async def test_deliver_attention_notifications_does_not_mark_delivered_on_ha_failure() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        item = AttentionItemRecord(
            household_id=household.id,
            entity_id="calendar.family",
            event_uid="e1",
            change_type="cancelled",
            recurrence_key="key-1",
            state="active",
            summary="Cancelled: Dentist",
            detail={},
        )
        session.add(item)
        await session.commit()
        item_id = item.id

    delivered = await deliver_attention_notifications(
        factory, settings=Settings(_env_file=None), ha_client=_notification_ha_client(accept=False)
    )
    assert delivered == 0

    async with factory() as session:
        item = await session.get(AttentionItemRecord, item_id)
        assert item is not None
        assert item.notified_record_version is None


async def test_deliver_attention_notifications_skips_acknowledged_and_dismissed_items() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        session.add_all(
            [
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e1",
                    change_type="cancelled",
                    recurrence_key="key-1",
                    state="acknowledged",
                    summary="Cancelled: Dentist",
                    detail={},
                ),
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e2",
                    change_type="cancelled",
                    recurrence_key="key-2",
                    state="dismissed",
                    summary="Cancelled: Piano",
                    detail={},
                ),
            ]
        )
        await session.commit()

    delivered = await deliver_attention_notifications(
        factory, settings=Settings(_env_file=None), ha_client=_notification_ha_client(accept=True)
    )
    assert delivered == 0


async def test_reconcile_unknown_activity_skips_rows_with_no_deterministic_expected_state() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        household = await _seeded_household(session)
        session.add(
            ActivityRecord(
                household_id=household.id,
                summary="switch.toggle on switch.office",
                outcome="unknown",
                detail={"domain": "switch", "service": "toggle", "entity_id": "switch.office"},
                occurred_at=datetime.now(UTC),
            )
        )
        await session.commit()

    resolved = await reconcile_unknown_activity(
        factory, settings=Settings(_env_file=None), ha_client=_reconciliation_ha_client(response_state="on")
    )
    assert resolved == 0

    async with factory() as session:
        activity = await session.scalar(select(ActivityRecord))
        assert activity is not None
        assert activity.outcome == "unknown"
    await engine.dispose()
