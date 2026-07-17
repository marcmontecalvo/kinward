from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.calendar import list_attention_items
from kinward.persistence.models import AttentionItemRecord, CalendarEventObservationRecord

#: Only "attention" exists today (v0's briefing surfaces active/acknowledged/recently
#: resolved attention items; a plain upcoming event with no condition is reported
#: separately as ``next_event_summary``, not as a list item) - kept as a Literal
#: rather than a bare ``str`` so a future item kind is a deliberate, typed addition.
BriefingItemKind = Literal["attention"]

# epic-5's priority order: required action, urgency, consequence if ignored, recency,
# confidence, household relevance. v0 approximates this with a fixed per-change-type
# tier (cancellations/RSVPs/conflicts genuinely require an action or response;
# informational time/location changes do not; resolved items sink to the bottom;
# plain upcoming events with no condition are lowest) and breaks ties within a tier by
# how soon the event happens, then how recently the item changed.
_ACTION_REQUIRED_CHANGE_TYPES = frozenset({"cancelled", "rsvp_required", "overlap", "back_to_back"})
_INFORMATIONAL_CHANGE_TYPES = frozenset({"time_changed", "location_changed"})

RECENTLY_RESOLVED_WINDOW = timedelta(hours=24)


def _tier(item: AttentionItemRecord) -> int:
    if item.state == "resolved":
        return 3
    if item.change_type in _ACTION_REQUIRED_CHANGE_TYPES:
        return 0
    if item.change_type in _INFORMATIONAL_CHANGE_TYPES:
        return 1
    return 2


@dataclass(frozen=True)
class BriefingItem:
    id: str
    kind: BriefingItemKind
    change_type: str | None
    state: str | None
    summary: str
    entity_id: str
    event_starts_at: datetime | None


@dataclass(frozen=True)
class Briefing:
    items: list[BriefingItem]
    active_attention_count: int
    next_event_summary: str | None
    next_event_starts_at: datetime | None
    text_summary: str


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _sort_key(item: AttentionItemRecord) -> tuple[int, datetime, float]:
    far_future = datetime.max.replace(tzinfo=UTC)
    starts_at = _aware(item.event_starts_at) if item.event_starts_at is not None else far_future
    return (_tier(item), starts_at, -_aware(item.updated_at).timestamp())


def _deterministic_summary(
    action_required: list[BriefingItem],
    informational: list[BriefingItem],
    resolved: list[BriefingItem],
    *,
    next_event_summary: str | None,
) -> str:
    """epic-5 Story 5.4: "a deterministic fallback summary exists when no model is
    available" - this is that fallback, and doubles as the policy-filtered structured
    text handed to a configured model for wording (Story 5.4: "if an LLM is used for
    wording, it receives policy-filtered structured facts only").
    """
    lines: list[str] = []
    if not action_required and not informational:
        lines.append("Nothing needs your attention right now.")
    else:
        if action_required:
            lines.append(f"{len(action_required)} item(s) need your attention:")
            lines.extend(f"- {item.summary}" for item in action_required)
        if informational:
            lines.append("Recent changes:")
            lines.extend(f"- {item.summary}" for item in informational)
    if resolved:
        lines.append("Recently resolved:")
        lines.extend(f"- {item.summary}" for item in resolved)
    if next_event_summary:
        lines.append(f"Next up: {next_event_summary}")
    return "\n".join(lines)


async def compute_briefing(
    session: AsyncSession, *, household_id: str, now: datetime | None = None
) -> Briefing:
    """The continuously-current briefing projection (Story 5.4): a read of current
    attention-item state plus the soonest upcoming event, never a second independent
    source of truth - both are read from state a calendar sync pass already wrote
    (``application/calendar.py``), not a fresh Home Assistant call of their own.
    Deterministic throughout - no model call, no judgment about importance beyond the
    fixed priority tiers above.
    """
    reference_time = now or datetime.now(UTC)
    attention_rows = await list_attention_items(session, household_id=household_id)

    recently_resolved_cutoff = reference_time - RECENTLY_RESOLVED_WINDOW
    visible_rows = [
        row
        for row in attention_rows
        if row.state != "resolved" or (row.resolved_at is not None and _aware(row.resolved_at) >= recently_resolved_cutoff)
    ]
    visible_rows.sort(key=_sort_key)

    items: list[BriefingItem] = []
    action_required: list[BriefingItem] = []
    informational: list[BriefingItem] = []
    resolved: list[BriefingItem] = []
    for row in visible_rows:
        item = BriefingItem(
            id=row.id,
            kind="attention",
            change_type=row.change_type,
            state=row.state,
            summary=row.summary,
            entity_id=row.entity_id,
            event_starts_at=_aware(row.event_starts_at) if row.event_starts_at is not None else None,
        )
        items.append(item)
        tier = _tier(row)
        if tier == 3:
            resolved.append(item)
        elif tier == 0:
            action_required.append(item)
        elif tier == 1:
            informational.append(item)

    active_count = sum(1 for row in attention_rows if row.state in ("active", "acknowledged"))

    next_observed = await session.scalar(
        select(CalendarEventObservationRecord)
        .where(
            CalendarEventObservationRecord.household_id == household_id,
            CalendarEventObservationRecord.starts_at >= reference_time,
        )
        .order_by(CalendarEventObservationRecord.starts_at)
        .limit(1)
    )
    next_event_summary = next_observed.summary if next_observed is not None else None
    next_event_starts_at = _aware(next_observed.starts_at) if next_observed is not None else None

    text_summary = _deterministic_summary(
        action_required, informational, resolved, next_event_summary=next_event_summary
    )

    return Briefing(
        items=items,
        active_attention_count=active_count,
        next_event_summary=next_event_summary,
        next_event_starts_at=next_event_starts_at,
        text_summary=text_summary,
    )
