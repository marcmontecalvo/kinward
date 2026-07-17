from datetime import datetime, timedelta, timezone

from kinward.domain.ha_observation import (
    DEFAULT_FRESHNESS_MAX_AGE,
    ObservedState,
    is_current,
    observe,
    observe_states,
)

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_observe_wraps_a_valid_row_with_availability_and_source() -> None:
    observed = observe(
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "last_changed": "2026-07-17T11:59:00+00:00",
            "attributes": {"friendly_name": "Kitchen Light"},
        },
        observed_at=NOW,
    )
    assert observed == ObservedState(
        entity_id="light.kitchen",
        state="on",
        attributes={"friendly_name": "Kitchen Light"},
        source="home_assistant",
        observed_at=NOW,
        last_changed=datetime(2026, 7, 17, 11, 59, 0, tzinfo=timezone.utc),
        available=True,
    )


def test_observe_marks_unavailable_and_unknown_states_as_unavailable() -> None:
    unavailable = observe({"entity_id": "light.office", "state": "unavailable"}, observed_at=NOW)
    unknown = observe({"entity_id": "sensor.attic", "state": "unknown"}, observed_at=NOW)
    assert unavailable is not None and unavailable.available is False
    assert unknown is not None and unknown.available is False


def test_observe_returns_none_for_malformed_rows() -> None:
    assert observe({"entity_id": "light.kitchen"}, observed_at=NOW) is None
    assert observe({"state": "on"}, observed_at=NOW) is None
    assert observe({"entity_id": 123, "state": "on"}, observed_at=NOW) is None


def test_observe_states_skips_malformed_rows_and_keeps_valid_ones() -> None:
    result = observe_states(
        [
            {"entity_id": "light.kitchen", "state": "on"},
            {"state": "missing entity id"},
            {"entity_id": "light.office", "state": "off"},
        ],
        observed_at=NOW,
    )
    assert [o.entity_id for o in result] == ["light.kitchen", "light.office"]


def test_is_current_requires_availability() -> None:
    observed = observe({"entity_id": "light.office", "state": "unavailable"}, observed_at=NOW)
    assert observed is not None
    assert is_current(observed, now=NOW) is False


def test_is_current_requires_freshness() -> None:
    observed = observe({"entity_id": "light.kitchen", "state": "on"}, observed_at=NOW)
    assert observed is not None
    just_in_time = NOW + DEFAULT_FRESHNESS_MAX_AGE
    too_late = NOW + DEFAULT_FRESHNESS_MAX_AGE + timedelta(seconds=1)
    assert is_current(observed, now=just_in_time) is True
    assert is_current(observed, now=too_late) is False


def test_is_current_true_for_a_live_available_observation() -> None:
    observed = observe({"entity_id": "light.kitchen", "state": "on"}, observed_at=NOW)
    assert observed is not None
    assert is_current(observed, now=NOW) is True
