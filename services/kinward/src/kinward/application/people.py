from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import PersonRecord


@dataclass(frozen=True)
class Person:
    id: str
    display_name: str


async def list_people(session: AsyncSession) -> list[Person]:
    rows = await session.execute(
        select(PersonRecord.id, PersonRecord.display_name).order_by(PersonRecord.display_name)
    )
    return [Person(id=row.id, display_name=row.display_name) for row in rows]
