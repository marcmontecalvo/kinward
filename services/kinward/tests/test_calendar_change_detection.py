from datetime import datetime, timezone

from kinward.domain.calendar_change_detection import (
    find_overlaps,
    has_meaningful_location_change,
    has_meaningful_time_change,
    is_rsvp_attention_worthy,
)
from kinward.domain.calendar_observation import ObservedEvent

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


def _event(
    *,
    entity_id: str = "calendar.family",
    event_uid: str = "event-1",
    summary: str = "Dentist",
    start: datetime,
    end: datetime,
    location: str | None = None,
) -> ObservedEvent:
    return ObservedEvent(
        entity_id=entity_id,
        event_uid=event_uid,
        summary=summary,
        start=start,
        end=end,
        location=location,
        all_day=False,
        rsvp_status=None,
        observed_at=NOW,
    )


def test_time_change_of_five_minutes_or_more_is_meaningful() -> None:
    old_start = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    new_start = datetime(2026, 7, 20, 9, 5, 0, tzinfo=timezone.utc)
    assert has_meaningful_time_change(
        old_start=old_start, old_end=old_end, new_start=new_start, new_end=old_end
    )


def test_time_change_smaller_than_five_minutes_is_ignored() -> None:
    old_start = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    new_start = datetime(2026, 7, 20, 9, 4, 0, tzinfo=timezone.utc)
    assert not has_meaningful_time_change(
        old_start=old_start, old_end=old_end, new_start=new_start, new_end=old_end
    )


def test_time_change_detects_end_time_moving_too() -> None:
    start = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)
    old_end = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)
    new_end = datetime(2026, 7, 20, 10, 30, 0, tzinfo=timezone.utc)
    assert has_meaningful_time_change(old_start=start, old_end=old_end, new_start=start, new_end=new_end)


def test_location_change_ignores_formatting_only_differences() -> None:
    assert not has_meaningful_location_change("123 Main St", "123 Main Street")


def test_location_change_detects_a_real_difference() -> None:
    assert has_meaningful_location_change("123 Main St", "456 Oak Ave")


def test_find_overlaps_detects_a_five_minute_or_more_overlap() -> None:
    first = _event(
        event_uid="a",
        summary="Soccer practice",
        start=datetime(2026, 7, 20, 16, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        location="Field 1",
    )
    second = _event(
        event_uid="b",
        summary="Piano lesson",
        start=datetime(2026, 7, 20, 16, 45, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 30, 0, tzinfo=timezone.utc),
        location="Music studio",
    )
    pairs = find_overlaps([first, second])
    assert len(pairs) == 1
    assert pairs[0].kind == "overlap"
    assert pairs[0].overlap_minutes == 15


def test_find_overlaps_ignores_overlaps_shorter_than_five_minutes() -> None:
    first = _event(
        event_uid="a",
        start=datetime(2026, 7, 20, 16, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
    )
    second = _event(
        event_uid="b",
        start=datetime(2026, 7, 20, 16, 58, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc),
    )
    assert find_overlaps([first, second]) == []


def test_find_overlaps_detects_back_to_back_different_locations_with_no_buffer() -> None:
    first = _event(
        event_uid="a",
        summary="Soccer practice",
        start=datetime(2026, 7, 20, 16, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        location="Field 1",
    )
    second = _event(
        event_uid="b",
        summary="Piano lesson",
        start=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc),
        location="Music studio",
    )
    pairs = find_overlaps([first, second])
    assert len(pairs) == 1
    assert pairs[0].kind == "back_to_back"


def test_find_overlaps_ignores_back_to_back_at_the_same_location() -> None:
    first = _event(
        event_uid="a",
        start=datetime(2026, 7, 20, 16, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        location="Field 1",
    )
    second = _event(
        event_uid="b",
        start=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc),
        location="Field 1",
    )
    assert find_overlaps([first, second]) == []


def test_find_overlaps_ignores_events_with_a_real_gap() -> None:
    first = _event(
        event_uid="a",
        start=datetime(2026, 7, 20, 16, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 17, 0, 0, tzinfo=timezone.utc),
        location="Field 1",
    )
    second = _event(
        event_uid="b",
        start=datetime(2026, 7, 20, 17, 30, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc),
        location="Music studio",
    )
    assert find_overlaps([first, second]) == []


def test_is_rsvp_attention_worthy_requires_both_conditions() -> None:
    assert is_rsvp_attention_worthy(needs_response=True, event_start_is_upcoming=True)
    assert not is_rsvp_attention_worthy(needs_response=True, event_start_is_upcoming=False)
    assert not is_rsvp_attention_worthy(needs_response=False, event_start_is_upcoming=True)
