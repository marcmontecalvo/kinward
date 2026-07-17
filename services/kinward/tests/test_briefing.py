from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.briefing import compute_briefing
from kinward.persistence.models import (
    AttentionItemRecord,
    Base,
    CalendarEventObservationRecord,
    HouseholdRecord,
)

NOW = datetime(2026, 7, 17, 12, 0, 0, tzinfo=timezone.utc)


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_household(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    return household


async def test_briefing_has_an_explicit_useful_empty_state() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert briefing.active_attention_count == 0
        assert briefing.items == []
        assert briefing.text_summary == "Nothing needs your attention right now."


async def test_action_required_items_are_prioritized_before_informational_ones() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        session.add_all(
            [
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e1",
                    change_type="location_changed",
                    recurrence_key="k1",
                    state="active",
                    summary="Location changed: Dentist",
                    detail={},
                    event_starts_at=NOW + timedelta(days=1),
                ),
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e2",
                    change_type="cancelled",
                    recurrence_key="k2",
                    state="active",
                    summary="Cancelled: Piano lesson",
                    detail={},
                    event_starts_at=NOW + timedelta(days=2),
                ),
            ]
        )
        await session.flush()

        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert [item.change_type for item in briefing.items] == ["cancelled", "location_changed"]
        assert briefing.active_attention_count == 2
        assert "2 item(s) need your attention" not in briefing.text_summary  # only 1 action-required item
        assert "Cancelled: Piano lesson" in briefing.text_summary


async def test_recently_resolved_items_are_included_but_sink_to_the_bottom() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        session.add(
            AttentionItemRecord(
                household_id=household.id,
                entity_id="calendar.family",
                event_uid="e1",
                change_type="overlap",
                recurrence_key="k1",
                state="resolved",
                summary="Soccer overlaps Piano",
                detail={},
                event_starts_at=NOW + timedelta(days=1),
                resolved_at=NOW - timedelta(hours=1),
            )
        )
        await session.flush()

        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert len(briefing.items) == 1
        assert briefing.items[0].state == "resolved"
        assert "Recently resolved" in briefing.text_summary


async def test_old_resolved_items_fall_out_of_the_briefing() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        session.add(
            AttentionItemRecord(
                household_id=household.id,
                entity_id="calendar.family",
                event_uid="e1",
                change_type="overlap",
                recurrence_key="k1",
                state="resolved",
                summary="Soccer overlaps Piano",
                detail={},
                resolved_at=NOW - timedelta(days=3),
            )
        )
        await session.flush()

        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert briefing.items == []


async def test_dismissed_and_expired_items_never_appear_in_the_briefing() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        session.add_all(
            [
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e1",
                    change_type="cancelled",
                    recurrence_key="k1",
                    state="dismissed",
                    summary="Cancelled: Old event",
                    detail={},
                ),
                AttentionItemRecord(
                    household_id=household.id,
                    entity_id="calendar.family",
                    event_uid="e2",
                    change_type="cancelled",
                    recurrence_key="k2",
                    state="expired",
                    summary="Cancelled: Even older event",
                    detail={},
                ),
            ]
        )
        await session.flush()

        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert briefing.items == []
        assert briefing.active_attention_count == 0


async def test_next_event_reflects_the_soonest_observed_event_even_without_attention() -> None:
    factory = await _factory()
    async with factory() as session:
        household = await _seed_household(session)
        session.add(
            CalendarEventObservationRecord(
                household_id=household.id,
                entity_id="calendar.family",
                event_uid="e1",
                summary="Soccer practice",
                location="Field 1",
                starts_at=NOW + timedelta(hours=4),
                ends_at=NOW + timedelta(hours=5),
                all_day=False,
                rsvp_status=None,
                observed_at=NOW,
            )
        )
        await session.flush()

        briefing = await compute_briefing(session, household_id=household.id, now=NOW)
        assert briefing.next_event_summary == "Soccer practice"
        assert briefing.next_event_starts_at == NOW + timedelta(hours=4)
        assert "Next up: Soccer practice" in briefing.text_summary
