from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from kinward.domain.calendar_observation import ObservedEvent, normalize_location

# epic-5: "Treat a change of five minutes or more as meaningful. Ignore changes
# smaller than five minutes as likely calendar churn."
TIME_CHANGE_THRESHOLD = timedelta(minutes=5)

# epic-5: "Treat any overlap of five minutes or more as meaningful."
OVERLAP_THRESHOLD = timedelta(minutes=5)

ChangeType = Literal[
    "cancelled", "time_changed", "location_changed", "overlap", "back_to_back", "rsvp_required"
]

# Deliberately Python, not an LLM (epic-5 Story 5.2: "An LLM does not decide whether a
# meaningful change occurred") - every function here is a pure, deterministic boolean
# or comparison over already-observed structured data.


def has_meaningful_time_change(
    *, old_start: datetime, old_end: datetime, new_start: datetime, new_end: datetime
) -> bool:
    """Whether the event's start or end moved by the significance threshold or more."""
    return abs(new_start - old_start) >= TIME_CHANGE_THRESHOLD or abs(new_end - old_end) >= TIME_CHANGE_THRESHOLD


def has_meaningful_location_change(old_location: str | None, new_location: str | None) -> bool:
    """Whether the event's location changed beyond formatting-only differences."""
    return normalize_location(old_location) != normalize_location(new_location)


@dataclass(frozen=True)
class OverlapPair:
    """Two currently-observed events that require attention together.

    ``kind`` distinguishes a genuine time overlap (``"overlap"``) from two
    back-to-back events at different locations with no travel buffer
    (``"back_to_back"``) - epic-5 treats both as meaningful but they are different
    conditions with different wording.
    """

    kind: Literal["overlap", "back_to_back"]
    first: ObservedEvent
    second: ObservedEvent
    overlap_minutes: float


def find_overlaps(events: list[ObservedEvent]) -> list[OverlapPair]:
    """Pairwise overlap/back-to-back detection across every currently observed event.

    Runs across every enabled calendar together (not per-calendar) since a conflict
    between two different household members' calendars is exactly the case worth
    surfacing. Quadratic in the event count, which is fine at household-calendar scale
    (a bounded lookahead window, not a full calendar history).
    """
    pairs: list[OverlapPair] = []
    ordered = sorted(events, key=lambda event: event.start)
    for index, first in enumerate(ordered):
        for second in ordered[index + 1 :]:
            if second.start >= first.end:
                gap = second.start - first.end
                if gap == timedelta(0) and has_meaningful_location_change(
                    first.location, second.location
                ):
                    pairs.append(OverlapPair(kind="back_to_back", first=first, second=second, overlap_minutes=0.0))
                # Events are sorted by start; once ``second`` starts at or after
                # ``first`` ends, no later event can overlap ``first`` either.
                break
            overlap_end = min(first.end, second.end)
            overlap_duration = overlap_end - second.start
            if overlap_duration >= OVERLAP_THRESHOLD:
                pairs.append(
                    OverlapPair(
                        kind="overlap",
                        first=first,
                        second=second,
                        overlap_minutes=overlap_duration.total_seconds() / 60,
                    )
                )
    return pairs


def is_rsvp_attention_worthy(*, needs_response: bool, event_start_is_upcoming: bool) -> bool:
    """epic-5: create an RSVP attention item only when a response is required, the
    invitation remains unanswered, and the event is still upcoming.
    """
    return needs_response and event_start_is_upcoming
