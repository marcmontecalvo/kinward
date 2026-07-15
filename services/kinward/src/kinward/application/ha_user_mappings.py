from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import AccountRecord, ActivityRecord, HaUserMappingRecord, PersonRecord


class MappingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


async def _has_account(session: AsyncSession, person_id: str) -> bool:
    account_id = await session.scalar(
        select(AccountRecord.id).where(AccountRecord.person_id == person_id)
    )
    return account_id is not None


async def upsert_mapping(
    session: AsyncSession, *, ha_user_id: str, person_id: str
) -> HaUserMappingRecord:
    person = await session.get(PersonRecord, person_id)
    if person is None:
        raise MappingError("person_not_found", "That Kinward profile does not exist.")
    if not await _has_account(session, person_id):
        raise MappingError(
            "person_not_account_bearing", "That profile has no account yet and cannot be mapped."
        )

    record = await session.scalar(
        select(HaUserMappingRecord).where(HaUserMappingRecord.ha_user_id == ha_user_id)
    )
    if record is None:
        record = HaUserMappingRecord(ha_user_id=ha_user_id, person_id=person_id)
        session.add(record)
    else:
        record.person_id = person_id
        record.record_version += 1

    session.add(
        ActivityRecord(
            household_id=person.household_id,
            summary="HA user mapping updated",
            outcome="completed",
            detail={"ha_user_id": ha_user_id},
        )
    )
    await session.flush()
    return record


async def remove_mapping(session: AsyncSession, *, ha_user_id: str) -> bool:
    record = await session.scalar(
        select(HaUserMappingRecord).where(HaUserMappingRecord.ha_user_id == ha_user_id)
    )
    if record is None:
        return False
    person = await session.get(PersonRecord, record.person_id)
    await session.delete(record)
    if person is not None:
        session.add(
            ActivityRecord(
                household_id=person.household_id,
                summary="HA user mapping removed",
                outcome="completed",
                detail={"ha_user_id": ha_user_id},
            )
        )
    await session.flush()
    return True


async def list_mappings(session: AsyncSession) -> list[HaUserMappingRecord]:
    result = await session.scalars(
        select(HaUserMappingRecord).order_by(HaUserMappingRecord.created_at)
    )
    return list(result)


async def resolve_mapping(session: AsyncSession, *, ha_user_id: str) -> str | None:
    """Fail-closed resolver: None for a missing mapping or a person with no account."""
    record = await session.scalar(
        select(HaUserMappingRecord).where(HaUserMappingRecord.ha_user_id == ha_user_id)
    )
    if record is None:
        return None
    if not await _has_account(session, record.person_id):
        return None
    return record.person_id
