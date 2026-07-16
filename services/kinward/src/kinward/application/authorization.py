from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.conversation import Unmapped
from kinward.persistence.models import PersonRecord


@dataclass(frozen=True)
class NotAdmin:
    """The caller is a synced person but not an HA-derived administrator - fail closed."""


async def resolve_person(session: AsyncSession, *, ha_user_id: str) -> PersonRecord | Unmapped:
    """Resolve an HA user id to the synced person it belongs to, or fail closed."""
    person = await session.scalar(select(PersonRecord).where(PersonRecord.ha_user_id == ha_user_id))
    if person is None:
        return Unmapped()
    return person


async def resolve_admin(session: AsyncSession, *, ha_user_id: str) -> PersonRecord | Unmapped | NotAdmin:
    """Resolve an HA user id to an administrator's person record, or fail closed.

    Kinward has no admin designation step of its own: this only reads the ``role``
    that ``people_sync.sync_people`` already reconciled from HA's own admin flag on
    the last sync pass. Any number of simultaneous admins is normal and expected.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    if person.role != "admin":
        return NotAdmin()
    return person
