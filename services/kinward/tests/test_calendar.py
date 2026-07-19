from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import kinward.application.calendar as calendar_module
from kinward.application.calendar import (
    AttentionItemNotFound,
    acknowledge_attention_item,
    dismiss_attention_item,
    list_attention_items,
    list_calendar_entities,
    list_items_needing_notification,
    mark_attention_item_notified,
    set_calendar_entity_enabled,
    sync_household_calendars,
)
from kinward.application.conversation import Unmapped
from kinward.config import Settings
from kinward.domain.attention_item import InvalidTransition
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.persistence.models import (
    AttentionItemRecord,
    Base,
    CalendarEventObservationRecord,
    ExternalAccountRecord,
    HouseholdRecord,
    PersonRecord,
)

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Marc",
        role="admin",
        profile_kind="adult",
        ha_person_id="ha-person-marc",
        ha_user_id="ha-user-marc",
    )
    session.add(person)
    await session.flush()
    return household, person


class _FakeCalendarClient(HomeAssistantClient):
    """An HA double serving whatever raw event list the test currently has stashed for
    each calendar entity - ignores the ``start``/``end`` query window entirely (tests
    control the fixture data directly rather than relying on window filtering)."""

    def __init__(self, events_by_entity: dict[str, list[dict]]) -> None:
        self._events_by_entity = events_by_entity

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path.startswith("/api/calendars/"):
                entity_id = path.removeprefix("/api/calendars/")
                return httpx.Response(200, json=self._events_by_entity.get(entity_id, []))
            if path == "/api/services/persistent_notification/create":
                return httpx.Response(200, json=[])
            return httpx.Response(404, json=None)

        super().__init__(
            base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
        )


def _event(
    *,
    uid: str,
    summary: str,
    start: datetime,
    end: datetime,
    location: str | None = None,
    rsvp_status: str | None = None,
) -> dict:
    return {
        "uid": uid,
        "summary": summary,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "location": location,
        "rsvp_status": rsvp_status,
    }


async def _enable_calendar(session, *, household_id: str, entity_id: str) -> None:  # type: ignore[no-untyped-def]
    await set_calendar_entity_enabled(
        session, household_id=household_id, entity_id=entity_id, enabled=True
    )


async def test_new_event_is_observed_without_creating_an_attention_item() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        events = {
            "calendar.family": [
                _event(
                    uid="e1",
                    summary="Dentist",
                    start=NOW + timedelta(days=1),
                    end=NOW + timedelta(days=1, hours=1),
                )
            ]
        }
        client = _FakeCalendarClient(events)

        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        observations = list(await session.scalars(select(CalendarEventObservationRecord)))
        assert len(observations) == 1
        items = await list_attention_items(session, household_id=household.id)
        assert items == []


async def test_meaningful_time_change_creates_an_attention_item() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        start = NOW + timedelta(days=1)
        events = {
            "calendar.family": [
                _event(uid="e1", summary="Dentist", start=start, end=start + timedelta(hours=1))
            ]
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        moved_start = start + timedelta(minutes=30)
        events["calendar.family"][0] = _event(
            uid="e1", summary="Dentist", start=moved_start, end=moved_start + timedelta(hours=1)
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert len(items) == 1
        assert items[0].change_type == "time_changed"
        assert items[0].state == "active"


async def test_time_change_smaller_than_five_minutes_is_ignored() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        start = NOW + timedelta(days=1)
        events = {
            "calendar.family": [
                _event(uid="e1", summary="Dentist", start=start, end=start + timedelta(hours=1))
            ]
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        moved_start = start + timedelta(minutes=2)
        events["calendar.family"][0] = _event(
            uid="e1", summary="Dentist", start=moved_start, end=moved_start + timedelta(hours=1)
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert items == []


async def test_repeated_sync_of_unchanged_state_does_not_duplicate_items() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        start = NOW + timedelta(days=1)
        moved_start = start + timedelta(minutes=30)
        events = {
            "calendar.family": [
                _event(uid="e1", summary="Dentist", start=start, end=start + timedelta(hours=1))
            ]
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        events["calendar.family"][0] = _event(
            uid="e1", summary="Dentist", start=moved_start, end=moved_start + timedelta(hours=1)
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert len(items) == 1


async def test_cancellation_creates_an_item_and_supersedes_other_open_items() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        start = NOW + timedelta(days=1)
        events = {
            "calendar.family": [
                _event(uid="e1", summary="Dentist", start=start, end=start + timedelta(hours=1))
            ]
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        moved_start = start + timedelta(minutes=30)
        events["calendar.family"][0] = _event(
            uid="e1", summary="Dentist", start=moved_start, end=moved_start + timedelta(hours=1)
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()
        pre_cancel_items = await list_attention_items(session, household_id=household.id)
        assert len(pre_cancel_items) == 1
        time_changed_id = pre_cancel_items[0].id

        events["calendar.family"] = []
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        superseded = await session.get(AttentionItemRecord, time_changed_id)
        assert superseded is not None
        assert superseded.state == "superseded"

        active_items = [
            item
            for item in await list_attention_items(session, household_id=household.id)
            if item.state == "active"
        ]
        assert len(active_items) == 1
        assert active_items[0].change_type == "cancelled"
        assert active_items[0].superseded_by_id is None


async def test_cancellation_of_an_already_past_event_is_not_flagged() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        past_start = NOW - timedelta(days=1)
        events = {
            "calendar.family": [
                _event(
                    uid="e1", summary="Old meeting", start=past_start, end=past_start + timedelta(hours=1)
                )
            ]
        }
        client = _FakeCalendarClient(events)
        # Seed the observation directly rather than syncing it in, since a real sync
        # would never fetch an already-past event in its lookahead window either.
        session.add(
            CalendarEventObservationRecord(
                household_id=household.id,
                entity_id="calendar.family",
                event_uid="e1",
                summary="Old meeting",
                location=None,
                starts_at=past_start,
                ends_at=past_start + timedelta(hours=1),
                all_day=False,
                rsvp_status=None,
                observed_at=NOW - timedelta(days=1),
            )
        )
        await session.flush()

        events["calendar.family"] = []
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert items == []


async def test_overlap_between_two_calendars_creates_an_item_and_resolves_when_gone() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.marc")
        start = NOW + timedelta(days=1, hours=16)
        events = {
            "calendar.family": [
                _event(uid="a", summary="Soccer", start=start, end=start + timedelta(hours=1))
            ],
            "calendar.marc": [
                _event(
                    uid="b",
                    summary="Piano",
                    start=start + timedelta(minutes=45),
                    end=start + timedelta(hours=1, minutes=30),
                )
            ],
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert len(items) == 1
        assert items[0].change_type == "overlap"
        assert items[0].state == "active"

        # Move the second event so it no longer overlaps - the item should resolve.
        events["calendar.marc"][0] = _event(
            uid="b",
            summary="Piano",
            start=start + timedelta(hours=2),
            end=start + timedelta(hours=3),
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        overlap_item = await session.get(AttentionItemRecord, items[0].id)
        assert overlap_item is not None
        assert overlap_item.state == "resolved"


async def test_rsvp_required_creates_an_item_and_resolves_once_answered() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        await _enable_calendar(session, household_id=household.id, entity_id="calendar.family")
        start = NOW + timedelta(days=2)
        events = {
            "calendar.family": [
                _event(
                    uid="e1",
                    summary="Birthday party",
                    start=start,
                    end=start + timedelta(hours=2),
                    rsvp_status="needs_action",
                )
            ]
        }
        client = _FakeCalendarClient(events)
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        items = await list_attention_items(session, household_id=household.id)
        assert len(items) == 1
        assert items[0].change_type == "rsvp_required"

        events["calendar.family"][0] = _event(
            uid="e1",
            summary="Birthday party",
            start=start,
            end=start + timedelta(hours=2),
            rsvp_status="accepted",
        )
        await sync_household_calendars(session, household_id=household.id, ha_client=client, now=NOW)
        await session.commit()

        resolved = await session.get(AttentionItemRecord, items[0].id)
        assert resolved is not None
        assert resolved.state == "resolved"


async def test_acknowledge_and_dismiss_transitions() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed(session)
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
        await session.flush()

        acknowledged = await acknowledge_attention_item(
            session, household_id=household.id, ha_user_id="ha-user-marc", item_id=item.id
        )
        assert isinstance(acknowledged, AttentionItemRecord)
        assert acknowledged.state == "acknowledged"

        dismissed = await dismiss_attention_item(
            session, household_id=household.id, ha_user_id="ha-user-marc", item_id=item.id
        )
        assert isinstance(dismissed, AttentionItemRecord)
        assert dismissed.state == "dismissed"

        # Already dismissed - cannot acknowledge a hidden item back without a new change.
        blocked = await acknowledge_attention_item(
            session, household_id=household.id, ha_user_id="ha-user-marc", item_id=item.id
        )
        assert isinstance(blocked, InvalidTransition)

        not_found = await acknowledge_attention_item(
            session, household_id=household.id, ha_user_id="ha-user-marc", item_id="missing"
        )
        assert isinstance(not_found, AttentionItemNotFound)

        unmapped = await acknowledge_attention_item(
            session, household_id=household.id, ha_user_id="unknown-user", item_id=item.id
        )
        assert isinstance(unmapped, Unmapped)


async def test_calendar_entities_can_be_enabled_and_disabled_independently() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
        client = _FakeCalendarClient({})

        await set_calendar_entity_enabled(
            session, household_id=household.id, entity_id="calendar.family", enabled=True
        )
        await set_calendar_entity_enabled(
            session, household_id=household.id, entity_id="calendar.work", enabled=False
        )
        statuses = await list_calendar_entities(session, household_id=household.id, ha_client=client)
        by_entity = {status.entity_id: status.enabled for status in statuses}
        assert by_entity["calendar.family"] is True
        assert by_entity["calendar.work"] is False


async def test_notification_dedup_only_flags_active_items_not_yet_notified() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed(session)
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
        await session.flush()

        pending = await list_items_needing_notification(session, household_id=household.id)
        assert [row.id for row in pending] == [item.id]

        await mark_attention_item_notified(
            session, item_id=item.id, record_version=item.record_version, now=NOW
        )
        await session.flush()

        pending_after = await list_items_needing_notification(session, household_id=household.id)
        assert pending_after == []

        item.summary = "Cancelled: Dentist (rescheduled)"
        item.record_version += 1
        await session.flush()

        pending_after_change = await list_items_needing_notification(session, household_id=household.id)
        assert [row.id for row in pending_after_change] == [item.id]


async def test_connected_external_account_events_sync_alongside_ha_calendars(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Epic 5 v1 roadmap item 1: a connected Google/Microsoft account's events flow
    through the exact same detection/attention pipeline as HA calendar entities, keyed
    by the synthetic ``"{provider}:{account_id}"`` entity_id - no HA client involvement,
    no ``CalendarEntityRecord`` opt-in row needed (connecting the account itself is the
    opt-in). ``fetch_external_account_events`` (the token-refresh/HTTP boundary) is
    monkeypatched here so this test stays about the wiring, not OAuth mechanics -
    ``test_accounts.py`` covers that boundary directly.
    """
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed(session)
        account = ExternalAccountRecord(
            household_id=household.id,
            owner_person_id=person.id,
            provider="google",
            provider_account_email="marc@example.com",
            scopes=[],
            access_token_encrypted="unused-in-this-test",
            refresh_token_encrypted=None,
            token_expires_at=NOW + timedelta(hours=1),
            status="connected",
        )
        session.add(account)
        await session.flush()
        account_id = account.id

        async def fake_fetch_external_account_events(session, *, account, start, end, settings):  # type: ignore[no-untyped-def]
            return [
                _event(
                    uid="g1",
                    summary="Standup",
                    start=NOW + timedelta(days=1),
                    end=NOW + timedelta(days=1, hours=1),
                )
            ]

        monkeypatch.setattr(
            calendar_module, "fetch_external_account_events", fake_fetch_external_account_events
        )

        settings = Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            account_token_encryption_key=Fernet.generate_key().decode(),
        )
        client = _FakeCalendarClient({})
        result = await sync_household_calendars(
            session, household_id=household.id, ha_client=client, settings=settings, now=NOW
        )
        await session.commit()

        assert result.entities_synced == 1
        assert result.events_observed == 1
        observations = list(await session.scalars(select(CalendarEventObservationRecord)))
        assert len(observations) == 1
        assert observations[0].entity_id == f"google:{account_id}"

        refreshed = await session.get(ExternalAccountRecord, account_id)
        assert refreshed is not None
        assert refreshed.last_synced_at == NOW


async def test_omitting_settings_skips_external_accounts() -> None:
    """A deployment with no external accounts configured (most tests, most
    deployments) never even queries ``ExternalAccountRecord`` - ``settings`` is
    optional precisely so callers don't have to thread one through for this."""
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed(session)
        session.add(
            ExternalAccountRecord(
                household_id=household.id,
                owner_person_id=person.id,
                provider="google",
                provider_account_email="marc@example.com",
                scopes=[],
                access_token_encrypted="unused-in-this-test",
                token_expires_at=NOW + timedelta(hours=1),
                status="connected",
            )
        )
        await session.flush()

        client = _FakeCalendarClient({})
        result = await sync_household_calendars(
            session, household_id=household.id, ha_client=client, now=NOW
        )
        await session.commit()

        assert result.entities_synced == 0
        observations = list(await session.scalars(select(CalendarEventObservationRecord)))
        assert observations == []
