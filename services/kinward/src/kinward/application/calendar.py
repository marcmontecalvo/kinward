from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.domain.attention_item import (
    OPEN_STATES,
    REACTIVATED_STATE,
    InvalidTransition,
    can_acknowledge,
    can_dismiss,
)
from kinward.domain.calendar_change_detection import (
    find_overlaps,
    has_meaningful_location_change,
    has_meaningful_time_change,
    is_rsvp_attention_worthy,
)
from kinward.domain.calendar_observation import ObservedEvent, observe_events, rsvp_needs_response
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.persistence.models import AttentionItemRecord, CalendarEntityRecord, CalendarEventObservationRecord

# How far ahead each sync pass looks for events - bounded so a household's entire
# calendar history isn't fetched every pass, generous enough to catch RSVP/overlap
# conditions on things scheduled more than a few days out.
SYNC_WINDOW = timedelta(days=14)

# An event that started this long ago no longer needs open attention - its useful
# window (epic-5 Core Concepts: "Expired: no longer relevant because its useful time
# window has passed") has ended once it has actually begun.
EXPIRE_GRACE_PERIOD = timedelta(0)


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    """SQLite round-trips ``DateTime(timezone=True)`` values as naive - normalize
    before comparing against a freshly-constructed aware ``datetime`` (same pattern as
    ``application/pending_actions.py``/``worker.py``).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _event_recurrence_key(*, entity_id: str, event_uid: str, change_type: str) -> str:
    raw = f"{entity_id}|{event_uid}|{change_type}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _pair_recurrence_key(*, first: ObservedEvent, second: ObservedEvent, kind: str) -> str:
    keys = sorted([f"{first.entity_id}|{first.event_uid}", f"{second.entity_id}|{second.event_uid}"])
    raw = f"{kind}|{keys[0]}|{keys[1]}"
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class CalendarEntityStatus:
    """One HA ``calendar.*`` entity, cross-referencing live HA discovery against
    Kinward's own enable/disable decision (Story 5.1: entities can be enabled or
    disabled independently; absence of a stored decision means "not yet enabled").
    """

    entity_id: str
    enabled: bool
    known_to_ha: bool


async def list_calendar_entities(
    session: AsyncSession, *, household_id: str, ha_client: HomeAssistantClient
) -> list[CalendarEntityStatus]:
    discovered = await ha_client.list_calendar_entities() if ha_client.enabled else []
    rows = await session.scalars(
        select(CalendarEntityRecord).where(CalendarEntityRecord.household_id == household_id)
    )
    by_entity = {row.entity_id: row for row in rows}
    entity_ids = sorted(set(discovered) | set(by_entity))
    return [
        CalendarEntityStatus(
            entity_id=entity_id,
            enabled=by_entity[entity_id].enabled if entity_id in by_entity else False,
            known_to_ha=entity_id in discovered,
        )
        for entity_id in entity_ids
    ]


async def set_calendar_entity_enabled(
    session: AsyncSession, *, household_id: str, entity_id: str, enabled: bool
) -> CalendarEntityRecord:
    row = await session.scalar(
        select(CalendarEntityRecord).where(
            CalendarEntityRecord.household_id == household_id,
            CalendarEntityRecord.entity_id == entity_id,
        )
    )
    if row is None:
        row = CalendarEntityRecord(household_id=household_id, entity_id=entity_id, enabled=enabled)
        session.add(row)
    else:
        row.enabled = enabled
        row.record_version += 1
    await session.flush()
    return row


async def _enabled_entity_ids(session: AsyncSession, *, household_id: str) -> list[str]:
    rows = await session.scalars(
        select(CalendarEntityRecord.entity_id).where(
            CalendarEntityRecord.household_id == household_id, CalendarEntityRecord.enabled.is_(True)
        )
    )
    return list(rows)


def _event_summary(event: ObservedEvent, *, change_type: str) -> str:
    when = event.start.strftime("%a %b %d") if event.all_day else event.start.strftime("%a %b %d, %I:%M %p")
    if change_type == "cancelled":
        return f"Cancelled: {event.summary} ({when})"
    if change_type == "time_changed":
        return f"Time changed: {event.summary} is now {when}"
    if change_type == "location_changed":
        return f"Location changed: {event.summary} ({event.location or 'no location'})"
    if change_type == "rsvp_required":
        return f"Response needed: {event.summary} ({when})"
    return f"{event.summary} ({when})"


async def _upsert_attention_item(
    session: AsyncSession,
    *,
    household_id: str,
    entity_id: str,
    event_uid: str,
    change_type: str,
    recurrence_key: str,
    summary: str,
    detail: dict[str, Any],
    event_starts_at: datetime | None,
    now: datetime,
) -> AttentionItemRecord:
    """One logical calendar condition has one active item (Story 5.3): update the
    existing open row in place when one exists; a terminal (resolved/expired/
    superseded) prior row is left as history and a fresh row is created instead, since
    a closed condition "returning" is a new occurrence, not a resurrection.
    """
    existing = await session.scalar(
        select(AttentionItemRecord)
        .where(
            AttentionItemRecord.household_id == household_id,
            AttentionItemRecord.recurrence_key == recurrence_key,
            AttentionItemRecord.state.in_(OPEN_STATES),
        )
        .order_by(AttentionItemRecord.created_at.desc())
        .limit(1)
    )
    if existing is not None:
        material_change = existing.summary != summary or existing.detail != detail
        existing.summary = summary
        existing.detail = detail
        existing.event_starts_at = event_starts_at
        if material_change:
            if existing.state != "active":
                existing.state = REACTIVATED_STATE
                existing.acknowledged_at = None
            existing.record_version += 1
            existing.updated_at = now
        return existing

    item = AttentionItemRecord(
        household_id=household_id,
        entity_id=entity_id,
        event_uid=event_uid,
        change_type=change_type,
        recurrence_key=recurrence_key,
        state="active",
        summary=summary,
        detail=detail,
        event_starts_at=event_starts_at,
    )
    session.add(item)
    await session.flush()
    return item


async def _supersede_other_open_items(
    session: AsyncSession, *, household_id: str, entity_id: str, event_uid: str, keep_id: str, now: datetime
) -> None:
    """A cancellation makes every other open concern about the same event moot."""
    rows = await session.scalars(
        select(AttentionItemRecord).where(
            AttentionItemRecord.household_id == household_id,
            AttentionItemRecord.entity_id == entity_id,
            AttentionItemRecord.event_uid == event_uid,
            AttentionItemRecord.state.in_(OPEN_STATES),
            AttentionItemRecord.id != keep_id,
        )
    )
    for row in rows:
        row.state = "superseded"
        row.superseded_by_id = keep_id
        row.record_version += 1
        row.updated_at = now


async def _resolve_open_items(
    session: AsyncSession, *, household_id: str, recurrence_key: str, now: datetime
) -> None:
    rows = await session.scalars(
        select(AttentionItemRecord).where(
            AttentionItemRecord.household_id == household_id,
            AttentionItemRecord.recurrence_key == recurrence_key,
            AttentionItemRecord.state.in_(OPEN_STATES),
        )
    )
    for row in rows:
        row.state = "resolved"
        row.resolved_at = now
        row.record_version += 1
        row.updated_at = now


@dataclass(frozen=True)
class SyncSummary:
    entities_synced: int
    events_observed: int
    attention_items_active: int


async def sync_household_calendars(
    session: AsyncSession,
    *,
    household_id: str,
    ha_client: HomeAssistantClient,
    now: datetime | None = None,
    window: timedelta = SYNC_WINDOW,
) -> SyncSummary:
    """Fetch every enabled HA calendar entity's events, detect meaningful changes
    against the last-known snapshot (Story 5.2), and create/update/resolve attention
    items (Story 5.3). Deterministic and LLM-free throughout - see
    ``domain/calendar_change_detection.py``.
    """
    sync_time = now or _now()
    entity_ids = await _enabled_entity_ids(session, household_id=household_id)

    all_current_events: list[ObservedEvent] = []
    per_entity_current: dict[str, dict[str, ObservedEvent]] = {}

    for entity_id in entity_ids:
        raw_events = await ha_client.calendar_events(entity_id, start=sync_time, end=sync_time + window)
        observed_events = observe_events(raw_events, entity_id=entity_id, observed_at=sync_time)
        per_entity_current[entity_id] = {event.event_uid: event for event in observed_events}
        all_current_events.extend(observed_events)

    for entity_id, current_by_uid in per_entity_current.items():
        previous_rows = list(
            await session.scalars(
                select(CalendarEventObservationRecord).where(
                    CalendarEventObservationRecord.household_id == household_id,
                    CalendarEventObservationRecord.entity_id == entity_id,
                )
            )
        )
        previous_by_uid = {row.event_uid: row for row in previous_rows}

        for event_uid, previous in previous_by_uid.items():
            if event_uid in current_by_uid:
                continue
            previous_start = _aware(previous.starts_at)
            if previous_start <= sync_time:
                # Fell out of the fetch window because it already happened - not a
                # cancellation, just history.
                continue
            key = _event_recurrence_key(entity_id=entity_id, event_uid=event_uid, change_type="cancelled")
            item = await _upsert_attention_item(
                session,
                household_id=household_id,
                entity_id=entity_id,
                event_uid=event_uid,
                change_type="cancelled",
                recurrence_key=key,
                summary=f"Cancelled: {previous.summary}",
                detail={"title": previous.summary, "was_scheduled_for": previous_start.isoformat()},
                event_starts_at=previous_start,
                now=sync_time,
            )
            await _supersede_other_open_items(
                session,
                household_id=household_id,
                entity_id=entity_id,
                event_uid=event_uid,
                keep_id=item.id,
                now=sync_time,
            )
            await session.delete(previous)

        for event_uid, current in current_by_uid.items():
            previous_observation = previous_by_uid.get(event_uid)
            if previous_observation is not None:
                if has_meaningful_time_change(
                    old_start=_aware(previous_observation.starts_at),
                    old_end=_aware(previous_observation.ends_at),
                    new_start=current.start,
                    new_end=current.end,
                ):
                    key = _event_recurrence_key(
                        entity_id=entity_id, event_uid=event_uid, change_type="time_changed"
                    )
                    await _upsert_attention_item(
                        session,
                        household_id=household_id,
                        entity_id=entity_id,
                        event_uid=event_uid,
                        change_type="time_changed",
                        recurrence_key=key,
                        summary=_event_summary(current, change_type="time_changed"),
                        detail={
                            "previous_start": _aware(previous_observation.starts_at).isoformat(),
                            "new_start": current.start.isoformat(),
                        },
                        event_starts_at=current.start,
                        now=sync_time,
                    )
                if has_meaningful_location_change(previous_observation.location, current.location):
                    key = _event_recurrence_key(
                        entity_id=entity_id, event_uid=event_uid, change_type="location_changed"
                    )
                    await _upsert_attention_item(
                        session,
                        household_id=household_id,
                        entity_id=entity_id,
                        event_uid=event_uid,
                        change_type="location_changed",
                        recurrence_key=key,
                        summary=_event_summary(current, change_type="location_changed"),
                        detail={
                            "previous_location": previous_observation.location,
                            "new_location": current.location,
                        },
                        event_starts_at=current.start,
                        now=sync_time,
                    )
                if rsvp_needs_response(previous_observation.rsvp_status) and not rsvp_needs_response(
                    current.rsvp_status
                ):
                    key = _event_recurrence_key(
                        entity_id=entity_id, event_uid=event_uid, change_type="rsvp_required"
                    )
                    await _resolve_open_items(
                        session, household_id=household_id, recurrence_key=key, now=sync_time
                    )
                previous_observation.summary = current.summary
                previous_observation.location = current.location
                previous_observation.starts_at = current.start
                previous_observation.ends_at = current.end
                previous_observation.all_day = current.all_day
                previous_observation.rsvp_status = current.rsvp_status
                previous_observation.observed_at = current.observed_at
                previous_observation.record_version += 1
            else:
                session.add(
                    CalendarEventObservationRecord(
                        household_id=household_id,
                        entity_id=entity_id,
                        event_uid=event_uid,
                        summary=current.summary,
                        location=current.location,
                        starts_at=current.start,
                        ends_at=current.end,
                        all_day=current.all_day,
                        rsvp_status=current.rsvp_status,
                        observed_at=current.observed_at,
                    )
                )

            if is_rsvp_attention_worthy(
                needs_response=rsvp_needs_response(current.rsvp_status),
                event_start_is_upcoming=current.start > sync_time,
            ):
                key = _event_recurrence_key(
                    entity_id=entity_id, event_uid=event_uid, change_type="rsvp_required"
                )
                await _upsert_attention_item(
                    session,
                    household_id=household_id,
                    entity_id=entity_id,
                    event_uid=event_uid,
                    change_type="rsvp_required",
                    recurrence_key=key,
                    summary=_event_summary(current, change_type="rsvp_required"),
                    detail={"rsvp_status": current.rsvp_status},
                    event_starts_at=current.start,
                    now=sync_time,
                )

    active_pair_keys: set[str] = set()
    for pair in find_overlaps(all_current_events):
        key = _pair_recurrence_key(first=pair.first, second=pair.second, kind=pair.kind)
        active_pair_keys.add(key)
        verb = "overlaps" if pair.kind == "overlap" else "is back-to-back with"
        await _upsert_attention_item(
            session,
            household_id=household_id,
            entity_id=pair.first.entity_id,
            event_uid=pair.first.event_uid,
            change_type=pair.kind,
            recurrence_key=key,
            summary=f"{pair.first.summary} {verb} {pair.second.summary}",
            detail={
                "first_summary": pair.first.summary,
                "second_summary": pair.second.summary,
                "overlap_minutes": pair.overlap_minutes,
            },
            event_starts_at=min(pair.first.start, pair.second.start),
            now=sync_time,
        )

    stale_overlap_items = await session.scalars(
        select(AttentionItemRecord).where(
            AttentionItemRecord.household_id == household_id,
            AttentionItemRecord.change_type.in_(("overlap", "back_to_back")),
            AttentionItemRecord.state.in_(OPEN_STATES),
        )
    )
    for row in stale_overlap_items:
        if row.recurrence_key in active_pair_keys:
            continue
        row.state = "resolved"
        row.resolved_at = sync_time
        row.record_version += 1
        row.updated_at = sync_time

    expirable = await session.scalars(
        select(AttentionItemRecord).where(
            AttentionItemRecord.household_id == household_id,
            AttentionItemRecord.state.in_(OPEN_STATES),
            AttentionItemRecord.event_starts_at.is_not(None),
        )
    )
    for row in expirable:
        assert row.event_starts_at is not None
        if _aware(row.event_starts_at) + EXPIRE_GRACE_PERIOD <= sync_time:
            row.state = "expired"
            row.record_version += 1
            row.updated_at = sync_time

    await session.flush()

    active_items = list(
        await session.scalars(
            select(AttentionItemRecord).where(
                AttentionItemRecord.household_id == household_id,
                AttentionItemRecord.state.in_(("active", "acknowledged")),
            )
        )
    )
    return SyncSummary(
        entities_synced=len(entity_ids),
        events_observed=len(all_current_events),
        attention_items_active=len(active_items),
    )


@dataclass(frozen=True)
class AttentionItemNotFound:
    """No such attention item, or it doesn't belong to this household - fail closed."""


AcknowledgeOutcome = Unmapped | AttentionItemNotFound | InvalidTransition | AttentionItemRecord
DismissOutcome = Unmapped | AttentionItemNotFound | InvalidTransition | AttentionItemRecord


async def acknowledge_attention_item(
    session: AsyncSession, *, household_id: str, ha_user_id: str, item_id: str
) -> AcknowledgeOutcome:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    item = await session.get(AttentionItemRecord, item_id)
    if item is None or item.household_id != household_id:
        return AttentionItemNotFound()
    if not can_acknowledge(item.state):
        return InvalidTransition("not_open", f"cannot acknowledge an item in state {item.state!r}")
    item.state = "acknowledged"
    item.acknowledged_at = _now()
    item.record_version += 1
    await session.flush()
    return item


async def dismiss_attention_item(
    session: AsyncSession, *, household_id: str, ha_user_id: str, item_id: str
) -> DismissOutcome:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    item = await session.get(AttentionItemRecord, item_id)
    if item is None or item.household_id != household_id:
        return AttentionItemNotFound()
    if not can_dismiss(item.state):
        return InvalidTransition("not_open", f"cannot dismiss an item in state {item.state!r}")
    item.state = "dismissed"
    item.record_version += 1
    await session.flush()
    return item


async def list_items_needing_notification(
    session: AsyncSession, *, household_id: str
) -> list[AttentionItemRecord]:
    """Attention items eligible for a Home Assistant push (Story 5.6): only currently
    ``active`` (never acknowledged/dismissed - the household has already seen or
    hidden those, and a dismissed item that changes enough to matter again is
    reactivated to ``active`` by ``_upsert_attention_item``, which is exactly what
    makes it eligible here too) and not yet notified at their current
    ``record_version`` - "the same unchanged attention item is not repeatedly pushed."
    """
    rows = await session.scalars(
        select(AttentionItemRecord).where(
            AttentionItemRecord.household_id == household_id, AttentionItemRecord.state == "active"
        )
    )
    return [
        row
        for row in rows
        if row.notified_record_version is None or row.notified_record_version < row.record_version
    ]


async def mark_attention_item_notified(
    session: AsyncSession, *, item_id: str, record_version: int, now: datetime
) -> None:
    item = await session.get(AttentionItemRecord, item_id)
    if item is None:
        return
    item.last_notified_at = now
    item.notified_record_version = record_version


async def list_attention_items(
    session: AsyncSession, *, household_id: str, include_resolved: bool = True
) -> list[AttentionItemRecord]:
    """Every attention item worth showing in a briefing: active/acknowledged always,
    plus recently-resolved ones (epic-5: "Recently resolved changes when still
    useful") when requested. Dismissed/expired/superseded items are never shown - they
    are intentionally hidden or historical only.
    """
    states = ["active", "acknowledged"]
    if include_resolved:
        states.append("resolved")
    rows = await session.scalars(
        select(AttentionItemRecord)
        .where(AttentionItemRecord.household_id == household_id, AttentionItemRecord.state.in_(states))
        .order_by(AttentionItemRecord.updated_at.desc())
    )
    return list(rows)
