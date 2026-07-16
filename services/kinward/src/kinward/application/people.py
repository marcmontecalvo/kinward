from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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


ProfileKind = Literal["adult", "teen", "child"]

# The privacy classification a synced person's records carry follows their age-based
# profile_kind directly - child records are private-child (see lifecycle.py), everyone
# else's are private-person. Household role (admin/member) is a separate, HA-derived
# axis untouched by this.
_CLASSIFICATION_FOR_PROFILE_KIND: dict[str, str] = {
    "adult": "private-person",
    "teen": "private-person",
    "child": "private-child",
}


@dataclass(frozen=True)
class PersonNotFound:
    """No such person in this household - fail closed."""


async def reclassify_person(
    session: AsyncSession, *, household_id: str, person_id: str, profile_kind: ProfileKind
) -> PersonRecord | PersonNotFound:
    person = await session.get(PersonRecord, person_id)
    if person is None or person.household_id != household_id:
        return PersonNotFound()
    person.profile_kind = profile_kind
    person.classification = _CLASSIFICATION_FOR_PROFILE_KIND[profile_kind]
    person.record_version += 1
    await session.flush()
    return person
