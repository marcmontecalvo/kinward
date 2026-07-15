from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import HouseholdRecord, PersonRecord


@dataclass(frozen=True)
class HouseholdSummary:
    id: str
    name: str
    adult_count: int
    child_count: int


async def fetch_household_summary(session: AsyncSession) -> HouseholdSummary | None:
    household = await session.scalar(select(HouseholdRecord))
    if household is None:
        return None
    adult_count = await session.scalar(
        select(func.count())
        .select_from(PersonRecord)
        .where(PersonRecord.household_id == household.id, PersonRecord.profile_kind == "adult")
    )
    child_count = await session.scalar(
        select(func.count())
        .select_from(PersonRecord)
        .where(PersonRecord.household_id == household.id, PersonRecord.profile_kind == "child")
    )
    return HouseholdSummary(
        id=household.id,
        name=household.name,
        adult_count=int(adult_count or 0),
        child_count=int(child_count or 0),
    )
