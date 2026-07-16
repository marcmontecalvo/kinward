from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from kinward.integrations.home_assistant import HomeAssistantClient

RECENT_DEVICE_DOMAINS: tuple[str, ...] = ("light", "switch")
RECENT_DEVICE_ELIGIBLE_STATES: tuple[str, ...] = ("on", "off")
RECENT_DEVICE_CUTOFF_MINUTES = 5

RECENT_TIMER_DOMAINS: tuple[str, ...] = ("timer",)
RECENT_TIMER_ELIGIBLE_STATES: tuple[str, ...] = ("active",)
# No recency cutoff for timers - a 30-minute timer is still "the" timer to cancel long
# after 5 minutes have passed; "currently active" is the filter, not recency.


@dataclass(frozen=True)
class ResolvedEntity:
    entity_id: str
    state: str
    last_changed: str  # ISO 8601, as reported by Home Assistant


@dataclass(frozen=True)
class NoEntityCandidate:
    """No eligible, non-stale entity matched anywhere - never invent one; the caller must ask
    for clarification instead of guessing."""


EntityResolution = ResolvedEntity | NoEntityCandidate


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def resolve_area_for_device(ha_client: HomeAssistantClient, *, device_id: str) -> str | None:
    """The area a Home Assistant device belongs to, via HA's own ``area_id()`` template
    function - Kinward has no entity/device/area registry client of its own."""
    rendered = await ha_client.render_template(
        "{{ area_id(device_id) }}", variables={"device_id": device_id}
    )
    if rendered is None:
        return None
    text = rendered.strip()
    if not text or text.lower() == "none":
        return None
    return text


async def entities_in_area(ha_client: HomeAssistantClient, *, area_id: str) -> frozenset[str]:
    """Entity ids belonging to an area, via HA's ``area_entities()`` template function."""
    rendered = await ha_client.render_template(
        "{{ area_entities(area_id) | join(',') }}", variables={"area_id": area_id}
    )
    if not rendered:
        return frozenset()
    return frozenset(entity_id for entity_id in rendered.strip().split(",") if entity_id)


def _eligible_candidates(
    states: Sequence[dict[str, Any]],
    *,
    domains: Sequence[str],
    eligible_states: Sequence[str],
    cutoff: datetime | None,
) -> list[tuple[str, str, datetime]]:
    candidates: list[tuple[str, str, datetime]] = []
    for entity in states:
        entity_id = entity.get("entity_id")
        state = entity.get("state")
        if not isinstance(entity_id, str) or not isinstance(state, str):
            continue
        if entity_id.split(".", 1)[0] not in domains:
            continue
        if state not in eligible_states:
            continue
        last_changed = _parse_timestamp(entity.get("last_changed"))
        if last_changed is None:
            continue
        if cutoff is not None and last_changed < cutoff:
            continue
        candidates.append((entity_id, state, last_changed))
    return candidates


async def _resolve_recent_entity(
    ha_client: HomeAssistantClient,
    *,
    states: Sequence[dict[str, Any]],
    domains: Sequence[str],
    eligible_states: Sequence[str],
    device_id: str | None,
    cutoff_minutes: int | None,
    as_of: datetime | None = None,
) -> EntityResolution:
    now = as_of or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=cutoff_minutes) if cutoff_minutes is not None else None
    candidates = _eligible_candidates(
        states, domains=domains, eligible_states=eligible_states, cutoff=cutoff
    )
    if not candidates:
        return NoEntityCandidate()

    if device_id:
        area = await resolve_area_for_device(ha_client, device_id=device_id)
        if area:
            area_entity_ids = await entities_in_area(ha_client, area_id=area)
            in_area = [c for c in candidates if c[0] in area_entity_ids]
            # An empty area intersection never overrides a real household-wide match - it
            # just means "nothing in-area," not "nothing anywhere."
            if in_area:
                candidates = in_area

    candidates.sort(key=lambda candidate: candidate[2], reverse=True)
    entity_id, state, last_changed = candidates[0]
    return ResolvedEntity(entity_id=entity_id, state=state, last_changed=last_changed.isoformat())


async def resolve_recent_device(
    ha_client: HomeAssistantClient,
    *,
    states: Sequence[dict[str, Any]],
    device_id: str | None,
    as_of: datetime | None = None,
) -> EntityResolution:
    """The most recently changed light/switch, preferring the caller's current area.

    v0 heuristic (ADR-002 sec. 3): ``last_changed`` proves the entity's state changed, not
    that Kinward caused it - an automation, physical switch, another HA user, or an HA
    restart could all produce a false "most recent" match. Acceptable given the short
    recency cutoff, area preference, and "no candidate" fallback below; not durable memory.

    ``as_of`` overrides "now" for tests; production callers leave it unset.
    """
    return await _resolve_recent_entity(
        ha_client,
        states=states,
        domains=RECENT_DEVICE_DOMAINS,
        eligible_states=RECENT_DEVICE_ELIGIBLE_STATES,
        device_id=device_id,
        cutoff_minutes=RECENT_DEVICE_CUTOFF_MINUTES,
        as_of=as_of,
    )


async def resolve_recent_timer(
    ha_client: HomeAssistantClient,
    *,
    states: Sequence[dict[str, Any]],
    device_id: str | None,
    as_of: datetime | None = None,
) -> EntityResolution:
    """The most recently started timer that is still active, preferring the caller's area.

    Any household member may reference or cancel a household timer - no ownership check is
    applied here (nor is one needed yet: nothing calls a cancellation path in this pass).
    """
    return await _resolve_recent_entity(
        ha_client,
        states=states,
        domains=RECENT_TIMER_DOMAINS,
        eligible_states=RECENT_TIMER_ELIGIBLE_STATES,
        device_id=device_id,
        cutoff_minutes=None,
        as_of=as_of,
    )
