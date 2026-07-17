from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.activity import MAX_ACTIVITY_LIMIT, list_activity
from kinward.application.conversation import Unmapped
from kinward.persistence.models import ActivityRecord, Base, HouseholdRecord, PersonRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    owner = PersonRecord(
        household_id=household.id,
        display_name="Marc",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-marc",
        ha_user_id="ha-user-marc",
    )
    other = PersonRecord(
        household_id=household.id,
        display_name="Lisa",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-lisa",
        ha_user_id="ha-user-lisa",
    )
    admin = PersonRecord(
        household_id=household.id,
        display_name="Dana",
        role="admin",
        profile_kind="adult",
        ha_person_id="ha-person-dana",
        ha_user_id="ha-user-dana",
    )
    session.add_all([owner, other, admin])
    await session.flush()
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session.add_all(
        [
            ActivityRecord(
                household_id=household.id,
                person_id=owner.id,
                summary="Owner's own action",
                outcome="executed",
                detail={},
                occurred_at=base_time,
            ),
            ActivityRecord(
                household_id=household.id,
                person_id=other.id,
                summary="Someone else's action",
                outcome="executed",
                detail={},
                occurred_at=base_time + timedelta(minutes=1),
            ),
            ActivityRecord(
                household_id=household.id,
                person_id=None,
                summary="Household-wide event with no owning person",
                outcome="completed",
                detail={},
                occurred_at=base_time + timedelta(minutes=2),
            ),
        ]
    )
    await session.flush()
    return household, owner, other, admin


async def test_list_activity_unmapped_caller_fails_closed():
    session_factory = await _factory()
    async with session_factory() as session:
        household, _owner, _other, _admin = await _seed(session)
        result = await list_activity(
            session, household_id=household.id, ha_user_id="ha-user-stranger"
        )
        assert isinstance(result, Unmapped)


async def test_list_activity_non_admin_sees_only_own_records():
    session_factory = await _factory()
    async with session_factory() as session:
        household, owner, _other, _admin = await _seed(session)
        result = await list_activity(
            session, household_id=household.id, ha_user_id=owner.ha_user_id
        )
        assert not isinstance(result, Unmapped)
        assert [record.summary for record in result] == ["Owner's own action"]


async def test_list_activity_admin_sees_whole_household_feed():
    session_factory = await _factory()
    async with session_factory() as session:
        household, _owner, _other, admin = await _seed(session)
        result = await list_activity(
            session, household_id=household.id, ha_user_id=admin.ha_user_id
        )
        assert not isinstance(result, Unmapped)
        assert len(result) == 3


async def test_list_activity_orders_most_recent_first():
    session_factory = await _factory()
    async with session_factory() as session:
        household, owner, _other, admin = await _seed(session)
        extra = ActivityRecord(
            household_id=household.id,
            person_id=owner.id,
            summary="Owner's newer action",
            outcome="executed",
            detail={},
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=1),
        )
        session.add(extra)
        await session.flush()

        result = await list_activity(
            session, household_id=household.id, ha_user_id=owner.ha_user_id
        )
        assert not isinstance(result, Unmapped)
        assert [record.summary for record in result] == [
            "Owner's newer action",
            "Owner's own action",
        ]


async def test_list_activity_limit_is_bounded_from_above():
    session_factory = await _factory()
    async with session_factory() as session:
        household, _owner, _other, admin = await _seed(session)
        result = await list_activity(
            session,
            household_id=household.id,
            ha_user_id=admin.ha_user_id,
            limit=MAX_ACTIVITY_LIMIT + 1000,
        )
        assert not isinstance(result, Unmapped)
        assert len(result) == 3


