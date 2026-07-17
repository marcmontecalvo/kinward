from datetime import datetime, timezone

from kinward.domain.calendar_observation import (
    ObservedEvent,
    normalize_location,
    observe_event,
    observe_events,
    rsvp_needs_response,
)

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_observe_event_wraps_a_valid_row() -> None:
    observed = observe_event(
        {
            "uid": "event-1",
            "summary": "Dentist",
            "start": "2026-07-20T09:00:00+00:00",
            "end": "2026-07-20T10:00:00+00:00",
            "location": "123 Main St",
        },
        entity_id="calendar.family",
        observed_at=NOW,
    )
    assert observed == ObservedEvent(
        entity_id="calendar.family",
        event_uid="event-1",
        summary="Dentist",
        start=datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc),
        location="123 Main St",
        all_day=False,
        rsvp_status=None,
        observed_at=NOW,
    )


def test_observe_event_falls_back_to_a_derived_uid_when_none_provided() -> None:
    observed = observe_event(
        {
            "summary": "Dentist",
            "start": "2026-07-20T09:00:00+00:00",
            "end": "2026-07-20T10:00:00+00:00",
        },
        entity_id="calendar.family",
        observed_at=NOW,
    )
    assert observed is not None
    assert observed.event_uid == "calendar.family|2026-07-20T09:00:00+00:00|dentist"


def test_observe_event_returns_none_for_malformed_rows() -> None:
    assert observe_event({"summary": "Dentist"}, entity_id="calendar.family", observed_at=NOW) is None
    assert (
        observe_event(
            {"start": "2026-07-20T09:00:00+00:00", "end": "2026-07-20T10:00:00+00:00"},
            entity_id="calendar.family",
            observed_at=NOW,
        )
        is None
    )


def test_observe_event_detects_all_day_events() -> None:
    observed = observe_event(
        {
            "summary": "Vacation",
            "start": {"date": "2026-07-20"},
            "end": {"date": "2026-07-21"},
        },
        entity_id="calendar.family",
        observed_at=NOW,
    )
    assert observed is not None
    assert observed.all_day is True


def test_observe_event_reads_blank_location_as_none() -> None:
    observed = observe_event(
        {
            "summary": "Dentist",
            "start": "2026-07-20T09:00:00+00:00",
            "end": "2026-07-20T10:00:00+00:00",
            "location": "   ",
        },
        entity_id="calendar.family",
        observed_at=NOW,
    )
    assert observed is not None
    assert observed.location is None


def test_observe_events_skips_malformed_rows_and_keeps_valid_ones() -> None:
    result = observe_events(
        [
            {"summary": "Dentist", "start": "2026-07-20T09:00:00+00:00", "end": "2026-07-20T10:00:00+00:00"},
            {"summary": "missing start/end"},
        ],
        entity_id="calendar.family",
        observed_at=NOW,
    )
    assert len(result) == 1
    assert result[0].summary == "Dentist"


def test_normalize_location_ignores_formatting_only_differences() -> None:
    assert normalize_location("123 Main St") == normalize_location("123 Main Street")
    assert normalize_location("123 MAIN ST.") == normalize_location("123 main st")
    assert normalize_location("123  Main   St") == normalize_location("123 Main St")


def test_normalize_location_treats_none_and_blank_as_equal() -> None:
    assert normalize_location(None) == normalize_location("   ")


def test_normalize_location_detects_a_real_difference() -> None:
    assert normalize_location("123 Main St") != normalize_location("456 Oak Ave")


def test_rsvp_needs_response_recognizes_common_unanswered_statuses() -> None:
    assert rsvp_needs_response("needs_action") is True
    assert rsvp_needs_response("NEEDS-ACTION") is True
    assert rsvp_needs_response("tentative") is True


def test_rsvp_needs_response_false_for_answered_or_absent_status() -> None:
    assert rsvp_needs_response("accepted") is False
    assert rsvp_needs_response("declined") is False
    assert rsvp_needs_response(None) is False
