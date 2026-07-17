from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Home Assistant reports calendar visibility all-or-nothing today (epic-5's v0 scope
# decision: "Accept Home Assistant's existing all-or-nothing calendar visibility
# model") - there is no per-attendee RSVP contract every calendar platform exposes, so
# ``rsvp_status`` is populated only when the raw HA event payload actually carries one
# (Google Calendar's integration is the common case); it is ``None``, never fabricated,
# for any platform that doesn't report it.
_NEEDS_RESPONSE_RSVP_STATUSES = frozenset({"needs_action", "needs-action", "tentative"})

# Common address-abbreviation pairs normalized before comparing locations for a
# "meaningful" change (epic-5: "Ignore formatting-only differences such as... common
# address abbreviation differences"). Deliberately small and literal rather than a
# general address-parsing library - good enough to stop "123 Main St" vs "123 Main
# Street" from being treated as a location change.
_ADDRESS_ABBREVIATIONS: dict[str, str] = {
    "street": "st",
    "avenue": "ave",
    "boulevard": "blvd",
    "drive": "dr",
    "road": "rd",
    "lane": "ln",
    "court": "ct",
    "place": "pl",
    "suite": "ste",
    "apartment": "apt",
    "building": "bldg",
    "floor": "fl",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
}

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCTUATION_RE = re.compile(r"[.,#]")


def normalize_location(value: str | None) -> str | None:
    """Fold formatting-only differences out of a location string before comparing it.

    Lower-cases, strips punctuation/extra whitespace, and expands a small fixed set of
    common address-abbreviation words - not a general address-parsing library, just
    enough to stop "123 Main St" and "123 Main Street" from registering as a change.
    Returns ``None`` for an absent/blank location so "no location" compares equal to
    itself without becoming the string ``"none"``.
    """
    if value is None:
        return None
    text = value.strip().lower()
    if not text:
        return None
    text = _PUNCTUATION_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    words = [_ADDRESS_ABBREVIATIONS.get(word, word) for word in text.split(" ")]
    return " ".join(words)


@dataclass(frozen=True)
class ObservedEvent:
    """One Home Assistant calendar event, wrapped with the identity/freshness metadata
    epic-5 Story 5.1 requires on top of HA's raw ``/api/calendars/{entity_id}`` row.

    ``event_uid`` is HA's own event ``uid`` when the platform provides one; platforms
    that don't are keyed on a stable fallback derived from entity/start/summary
    (``_fallback_event_uid``) rather than treating every sync as a brand new event.
    """

    entity_id: str
    event_uid: str
    summary: str
    start: datetime
    end: datetime
    location: str | None
    all_day: bool
    rsvp_status: str | None
    observed_at: datetime


def _fallback_event_uid(*, entity_id: str, start: datetime, summary: str) -> str:
    return f"{entity_id}|{start.isoformat()}|{summary.strip().lower()}"


def _parse_timestamp(value: object) -> datetime | None:
    if isinstance(value, dict):
        value = value.get("dateTime") or value.get("date")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_all_day(raw_start: object) -> bool:
    return isinstance(raw_start, dict) and "date" in raw_start and "dateTime" not in raw_start


def observe_event(raw: dict[str, Any], *, entity_id: str, observed_at: datetime) -> ObservedEvent | None:
    """Wrap one raw HA calendar event row. Returns ``None`` for a malformed row (missing
    a parseable start/end or summary) - the caller skips these rather than guessing.
    """
    raw_start = raw.get("start")
    raw_end = raw.get("end")
    start = _parse_timestamp(raw_start)
    end = _parse_timestamp(raw_end)
    summary = raw.get("summary")
    if start is None or end is None or not isinstance(summary, str):
        return None

    location = raw.get("location")
    location = location if isinstance(location, str) and location.strip() else None

    uid = raw.get("uid")
    event_uid = uid if isinstance(uid, str) and uid.strip() else _fallback_event_uid(
        entity_id=entity_id, start=start, summary=summary
    )

    rsvp_status = raw.get("rsvp_status") or raw.get("response_status")
    rsvp_status = rsvp_status if isinstance(rsvp_status, str) and rsvp_status.strip() else None

    return ObservedEvent(
        entity_id=entity_id,
        event_uid=event_uid,
        summary=summary,
        start=start,
        end=end,
        location=location,
        all_day=_is_all_day(raw_start),
        rsvp_status=rsvp_status,
        observed_at=observed_at,
    )


def observe_events(
    raw_events: list[dict[str, Any]], *, entity_id: str, observed_at: datetime
) -> list[ObservedEvent]:
    observed = (observe_event(raw, entity_id=entity_id, observed_at=observed_at) for raw in raw_events)
    return [event for event in observed if event is not None]


def rsvp_needs_response(rsvp_status: str | None) -> bool:
    """Whether the raw RSVP signal (when a calendar platform reports one at all) means
    "a response is required and hasn't been given" - epic-5's RSVP significance rule.
    """
    return rsvp_status is not None and rsvp_status.lower() in _NEEDS_RESPONSE_RSVP_STATUSES
