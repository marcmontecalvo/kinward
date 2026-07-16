from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.domain.admin_invariant import validate_admin_removal
from kinward.persistence.models import ActivityRecord, PersonRecord


@dataclass(frozen=True)
class PersonNotFound:
    """No such person in this household - fail closed."""


@dataclass(frozen=True)
class AdminInvariantBlocked:
    code: str
    message: str


@dataclass(frozen=True)
class Deleted:
    person_id: str


async def _count_admins(session: AsyncSession, *, household_id: str) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(PersonRecord)
        .where(PersonRecord.household_id == household_id, PersonRecord.role == "admin")
    )
    return int(count or 0)


async def delete_person(
    session: AsyncSession, *, household_id: str, person_id: str
) -> Deleted | PersonNotFound | AdminInvariantBlocked:
    """Delete a synced person, refusing to leave the household with zero administrators.

    Kinward derives admin role live from HA on every sync pass, so any number of
    people can be admins at once; the only invariant worth enforcing here is that
    at least one always remains. Deletion is a deliberate admin action, distinct
    from HA person sync, which never deletes on its own (see people_sync).
    """
    person = await session.get(PersonRecord, person_id)
    if person is None or person.household_id != household_id:
        return PersonNotFound()

    admin_count = await _count_admins(session, household_id=household_id)
    valid, violation = validate_admin_removal(
        admin_count_before=admin_count, person_being_removed_is_admin=person.role == "admin"
    )
    if not valid:
        assert violation is not None
        return AdminInvariantBlocked(code=violation.code, message=violation.message)

    session.add(
        ActivityRecord(
            household_id=household_id,
            person_id=None,
            summary="Person deleted",
            outcome="completed",
            detail={"deleted_person_id": person_id, "role": person.role},
        )
    )
    await session.delete(person)
    await session.flush()
    return Deleted(person_id=person_id)
