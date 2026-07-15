from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import AccountRecord, PersonRecord


@dataclass(frozen=True)
class AccountBearingPerson:
    id: str
    display_name: str


async def list_account_bearing_people(session: AsyncSession) -> list[AccountBearingPerson]:
    rows = await session.execute(
        select(PersonRecord.id, PersonRecord.display_name)
        .join(AccountRecord, AccountRecord.person_id == PersonRecord.id)
        .order_by(PersonRecord.display_name)
    )
    return [AccountBearingPerson(id=row.id, display_name=row.display_name) for row in rows]
