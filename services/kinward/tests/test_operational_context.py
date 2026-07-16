from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from kinward.application.operational_context import (
    NoEntityCandidate,
    ResolvedEntity,
    entities_in_area,
    resolve_area_for_device,
    resolve_recent_device,
    resolve_recent_timer,
)
from kinward.integrations.home_assistant import HomeAssistantClient

NOW = datetime(2026, 7, 16, 12, 10, 0, tzinfo=timezone.utc)


def _iso(delta: timedelta) -> str:
    return (NOW + delta).isoformat()


def _disabled_client() -> HomeAssistantClient:
    return HomeAssistantClient(base_url=None, token=None)


def _client_with_handler(handler) -> HomeAssistantClient:  # type: ignore[no-untyped-def]
    return HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )


async def test_resolve_recent_device_picks_most_recently_changed_eligible_entity() -> None:
    states = [
        {"entity_id": "light.office", "state": "on", "last_changed": _iso(-timedelta(minutes=1))},
        {"entity_id": "switch.kitchen", "state": "on", "last_changed": _iso(-timedelta(minutes=3))},
    ]
    result = await resolve_recent_device(
        _disabled_client(), states=states, device_id=None, as_of=NOW
    )
    assert result == ResolvedEntity(
        entity_id="light.office", state="on", last_changed=_iso(-timedelta(minutes=1))
    )


async def test_resolve_recent_device_excludes_ineligible_domains_and_states() -> None:
    states = [
        {"entity_id": "sensor.temperature", "state": "on", "last_changed": _iso(-timedelta(seconds=1))},
        {"entity_id": "light.office", "state": "unavailable", "last_changed": _iso(-timedelta(seconds=1))},
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == NoEntityCandidate()


async def test_resolve_recent_device_excludes_stale_entities_past_cutoff() -> None:
    states = [
        {"entity_id": "light.office", "state": "on", "last_changed": _iso(-timedelta(minutes=20))},
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == NoEntityCandidate()


async def test_resolve_recent_device_entity_at_exact_cutoff_boundary_is_included() -> None:
    states = [
        {"entity_id": "light.office", "state": "on", "last_changed": _iso(-timedelta(minutes=5))},
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == ResolvedEntity(
        entity_id="light.office", state="on", last_changed=_iso(-timedelta(minutes=5))
    )


async def test_resolve_recent_device_entity_just_past_cutoff_is_excluded() -> None:
    states = [
        {
            "entity_id": "light.office",
            "state": "on",
            "last_changed": _iso(-timedelta(minutes=5, seconds=1)),
        },
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == NoEntityCandidate()


async def test_resolve_recent_timer_has_no_recency_cutoff() -> None:
    states = [
        {"entity_id": "timer.kitchen", "state": "active", "last_changed": _iso(-timedelta(minutes=45))},
    ]
    result = await resolve_recent_timer(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == ResolvedEntity(
        entity_id="timer.kitchen", state="active", last_changed=_iso(-timedelta(minutes=45))
    )


async def test_resolve_recent_timer_excludes_idle_timers() -> None:
    states = [
        {"entity_id": "timer.kitchen", "state": "idle", "last_changed": _iso(-timedelta(minutes=1))},
    ]
    result = await resolve_recent_timer(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == NoEntityCandidate()


async def test_no_candidate_when_states_are_empty() -> None:
    assert await resolve_recent_device(
        _disabled_client(), states=[], device_id=None, as_of=NOW
    ) == NoEntityCandidate()
    assert await resolve_recent_timer(
        _disabled_client(), states=[], device_id=None, as_of=NOW
    ) == NoEntityCandidate()


async def test_malformed_state_rows_are_skipped_not_erroring() -> None:
    states = [
        {"entity_id": "light.office", "state": "on"},  # missing last_changed
        {"entity_id": "light.office", "state": "on", "last_changed": "not-a-timestamp"},
        {"entity_id": 123, "state": "on", "last_changed": _iso(timedelta())},
        {"entity_id": "light.office"},  # missing state
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == NoEntityCandidate()


async def test_resolve_area_for_device_parses_rendered_template() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/template"
        return httpx.Response(200, text="office")

    client = _client_with_handler(handler)
    assert await resolve_area_for_device(client, device_id="device-1") == "office"


async def test_resolve_area_for_device_treats_none_response_as_unresolved() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="None")

    client = _client_with_handler(handler)
    assert await resolve_area_for_device(client, device_id="device-1") is None


async def test_resolve_area_for_device_returns_none_when_ha_disabled() -> None:
    assert await resolve_area_for_device(_disabled_client(), device_id="device-1") is None


async def test_entities_in_area_splits_comma_joined_response() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="light.office,switch.office_lamp")

    client = _client_with_handler(handler)
    result = await entities_in_area(client, area_id="office")
    assert result == frozenset({"light.office", "switch.office_lamp"})


async def test_entities_in_area_empty_response_is_empty_set() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="")

    client = _client_with_handler(handler)
    assert await entities_in_area(client, area_id="office") == frozenset()


async def test_resolve_recent_device_prefers_current_area_match() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.content.decode()
        if "area_id(device_id)" in payload:
            return httpx.Response(200, text="office")
        if "area_entities" in payload:
            return httpx.Response(200, text="light.office")
        raise AssertionError(f"unexpected template request: {payload}")

    client = _client_with_handler(handler)
    states = [
        {"entity_id": "light.office", "state": "on", "last_changed": _iso(-timedelta(minutes=4))},
        {"entity_id": "switch.kitchen", "state": "on", "last_changed": _iso(-timedelta(minutes=1))},
    ]
    result = await resolve_recent_device(client, states=states, device_id="device-1", as_of=NOW)
    assert result == ResolvedEntity(
        entity_id="light.office", state="on", last_changed=_iso(-timedelta(minutes=4))
    )


async def test_resolve_recent_device_falls_back_to_household_wide_when_area_has_no_match() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.content.decode()
        if "area_id(device_id)" in payload:
            return httpx.Response(200, text="office")
        if "area_entities" in payload:
            return httpx.Response(200, text="light.bedroom")
        raise AssertionError(f"unexpected template request: {payload}")

    client = _client_with_handler(handler)
    states = [
        {"entity_id": "switch.kitchen", "state": "on", "last_changed": _iso(-timedelta(minutes=1))},
    ]
    result = await resolve_recent_device(client, states=states, device_id="device-1", as_of=NOW)
    assert result == ResolvedEntity(
        entity_id="switch.kitchen", state="on", last_changed=_iso(-timedelta(minutes=1))
    )


async def test_resolve_recent_device_household_wide_when_device_id_none() -> None:
    states = [
        {"entity_id": "light.office", "state": "on", "last_changed": _iso(-timedelta(minutes=1))},
    ]
    result = await resolve_recent_device(_disabled_client(), states=states, device_id=None, as_of=NOW)
    assert result == ResolvedEntity(
        entity_id="light.office", state="on", last_changed=_iso(-timedelta(minutes=1))
    )
