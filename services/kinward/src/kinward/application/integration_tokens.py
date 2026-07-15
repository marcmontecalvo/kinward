from __future__ import annotations

from datetime import datetime, timezone
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.bootstrap import capability_hash
from kinward.persistence.models import IntegrationTokenRecord


async def create_token(session: AsyncSession, name: str) -> tuple[IntegrationTokenRecord, str]:
    plaintext = secrets.token_urlsafe(32)
    record = IntegrationTokenRecord(name=name.strip(), token_hash=capability_hash(plaintext))
    session.add(record)
    await session.flush()
    return record, plaintext


async def verify_token(session: AsyncSession, plaintext: str) -> IntegrationTokenRecord | None:
    record = await session.scalar(
        select(IntegrationTokenRecord).where(
            IntegrationTokenRecord.token_hash == capability_hash(plaintext)
        )
    )
    if record is None or record.revoked_at is not None:
        return None
    record.last_used_at = datetime.now(timezone.utc)
    return record


async def revoke_token(session: AsyncSession, token_id: str) -> bool:
    record = await session.get(IntegrationTokenRecord, token_id)
    if record is None or record.revoked_at is not None:
        return False
    record.revoked_at = datetime.now(timezone.utc)
    return True


async def list_tokens(session: AsyncSession) -> list[IntegrationTokenRecord]:
    result = await session.scalars(
        select(IntegrationTokenRecord).order_by(IntegrationTokenRecord.created_at)
    )
    return list(result)
