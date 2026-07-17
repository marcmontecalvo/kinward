from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.persistence.models import ActivityRecord

DEFAULT_ACTIVITY_LIMIT = 50
MAX_ACTIVITY_LIMIT = 200


async def list_activity(
    session: AsyncSession,
    *,
    household_id: str,
    ha_user_id: str,
    limit: int = DEFAULT_ACTIVITY_LIMIT,
) -> list[ActivityRecord] | Unmapped:
    """The caller's own visible activity, most recent first.

    A current HA-derived admin (cross-cutting rule 4) sees every household
    record; anyone else sees only records tied to their own ``person_id``,
    never another person's. Authorization is applied as a query filter, not a
    post-filter, so a non-admin caller's query never touches another
    person's row and cannot leak how many hidden records exist (epics.md
    Story 8.3: "leaks no unauthorized counts or facets").
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person

    bounded_limit = max(1, min(limit, MAX_ACTIVITY_LIMIT))
    query = select(ActivityRecord).where(ActivityRecord.household_id == household_id)
    if person.role != "admin":
        query = query.where(ActivityRecord.person_id == person.id)
    query = query.order_by(ActivityRecord.occurred_at.desc()).limit(bounded_limit)

    records = await session.scalars(query)
    return list(records)
