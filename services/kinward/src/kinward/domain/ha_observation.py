from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# HA reports both of these as "not a real reading" - neither may ever be presented to a
# household member as the entity's current state (epics.md Story 7.2: "Unavailable or
# stale state cannot be represented as current").
UNAVAILABLE_STATES: frozenset[str] = frozenset({"unavailable", "unknown"})

DEFAULT_FRESHNESS_MAX_AGE = timedelta(minutes=5)


@dataclass(frozen=True)
class ObservedState:
    """One HA entity's state, wrapped with the source/observation-time/availability/freshness
    metadata Story 7.2 requires on top of HA's raw ``/api/states`` row.

    ``source`` is always ``"home_assistant"`` today - Kinward has exactly one state provider -
    but is modeled explicitly since the story frames this as a "provider-neutral port"; a future
    non-HA source would populate it differently rather than needing a new shape.
    """

    entity_id: str
    state: str
    attributes: dict[str, Any]
    source: str
    observed_at: datetime
    last_changed: datetime | None
    available: bool


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def observe(raw: dict[str, Any], *, observed_at: datetime) -> ObservedState | None:
    """Wrap one raw HA state row. Returns ``None`` for a malformed row (missing/non-string
    ``entity_id``/``state``) - the caller skips these, matching the pre-existing raw-dump path.
    """
    entity_id = raw.get("entity_id")
    state = raw.get("state")
    if not isinstance(entity_id, str) or not isinstance(state, str):
        return None
    attributes = raw.get("attributes")
    return ObservedState(
        entity_id=entity_id,
        state=state,
        attributes=attributes if isinstance(attributes, dict) else {},
        source="home_assistant",
        observed_at=observed_at,
        last_changed=_parse_timestamp(raw.get("last_changed")),
        available=state not in UNAVAILABLE_STATES,
    )


def observe_states(raw_states: list[dict[str, Any]], *, observed_at: datetime) -> list[ObservedState]:
    observed = (observe(raw, observed_at=observed_at) for raw in raw_states)
    return [state for state in observed if state is not None]


def is_current(
    observed: ObservedState, *, now: datetime, max_age: timedelta = DEFAULT_FRESHNESS_MAX_AGE
) -> bool:
    """Whether ``observed`` may be presented as the entity's *current* state right now.

    Requires both availability (HA isn't reporting "unavailable"/"unknown") and freshness (the
    observation was fetched recently enough relative to ``now``). Kinward has no caching layer
    yet - every read is fetched live within the same request - so this is always true in
    practice today; it exists so a future caching/batching path can't silently start presenting
    a held-over reading as current without an explicit freshness check catching it.
    """
    if not observed.available:
        return False
    return (now - observed.observed_at) <= max_age
