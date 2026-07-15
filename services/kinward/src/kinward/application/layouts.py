from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Protocol

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import (
    ActivityRecord,
    HouseholdRecord,
    LayoutActivationAttemptRecord,
    OutboxMessageRecord,
    PersonRecord,
    SurfaceLayoutRecord,
)


class LayoutActivationError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class LayoutUnitOfWork(Protocol):
    session: AsyncSession

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@dataclass
class SqlAlchemyLayoutUnitOfWork:
    session: AsyncSession

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


@dataclass(frozen=True)
class ActivateLayoutCommand:
    scope: str
    scope_id: str
    surface_class: str
    expected_version: int
    layout_id: str
    configuration: dict[str, Any]
    idempotency_key: str

    def fingerprint(self) -> str:
        value = {
            "scope": self.scope,
            "scope_id": self.scope_id,
            "surface_class": self.surface_class,
            "expected_version": self.expected_version,
            "layout_id": self.layout_id,
            "configuration": self.configuration,
        }
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


async def activate_layout(
    unit_of_work: LayoutUnitOfWork, command: ActivateLayoutCommand
) -> dict[str, Any]:
    session = unit_of_work.session
    if session.get_bind().dialect.name == "sqlite":
        await session.execute(text("BEGIN IMMEDIATE"))
    fingerprint = command.fingerprint()
    replay = await session.scalar(
        select(LayoutActivationAttemptRecord).where(
            LayoutActivationAttemptRecord.idempotency_key == command.idempotency_key
        )
    )
    if replay is not None:
        if replay.request_fingerprint != fingerprint:
            raise LayoutActivationError("idempotency_conflict", "That layout request identity was already used.")
        return dict(replay.result)

    household_count = await session.scalar(select(func.count()).select_from(HouseholdRecord))
    if household_count != 1:
        raise LayoutActivationError("household_unavailable", "A configured household is required.")
    household = await session.scalar(select(HouseholdRecord))
    if household is None:
        raise LayoutActivationError("household_unavailable", "A configured household is required.")
    if command.scope == "person-surface":
        owner = await session.scalar(
            select(PersonRecord).where(
                PersonRecord.id == command.scope_id,
                PersonRecord.household_id == household.id,
            )
        )
        if owner is None:
            raise LayoutActivationError("scope_invalid", "The layout scope is not available.")

    record = await session.scalar(
        select(SurfaceLayoutRecord).where(
            SurfaceLayoutRecord.household_id == household.id,
            SurfaceLayoutRecord.scope == command.scope,
            SurfaceLayoutRecord.scope_id == command.scope_id,
            SurfaceLayoutRecord.surface_class == command.surface_class,
        )
    )
    current_version = record.version if record is not None else 0
    if current_version != command.expected_version:
        raise LayoutActivationError(
            "version_conflict",
            "The active layout changed. Reload it before trying again.",
            retryable=True,
        )
    next_version = current_version + 1
    if record is None:
        record = SurfaceLayoutRecord(
            household_id=household.id,
            scope=command.scope,
            scope_id=command.scope_id,
            surface_class=command.surface_class,
            name=command.layout_id,
            version=next_version,
            configuration=command.configuration,
        )
        session.add(record)
    else:
        record.name = command.layout_id
        record.version = next_version
        record.record_version += 1
        record.configuration = command.configuration
        record.active = True
    await session.flush()
    result = {
        "assignment_id": record.id,
        "assignment_version": next_version,
        "layout_id": command.layout_id,
        "scope": command.scope,
        "surface_class": command.surface_class,
    }
    session.add_all(
        [
            LayoutActivationAttemptRecord(
                idempotency_key=command.idempotency_key,
                request_fingerprint=fingerprint,
                result=result,
            ),
            ActivityRecord(
                household_id=household.id,
                summary="Surface layout activated",
                outcome="completed",
                detail={"classification": "system-operational", "scope": command.scope},
            ),
            OutboxMessageRecord(
                topic="surface.layout.activated",
                payload={"assignment_id": record.id, "classification": "system-operational"},
            ),
        ]
    )
    await unit_of_work.commit()
    return result


async def get_household_surface_layout(
    session: AsyncSession, *, surface_class: str
) -> dict[str, Any] | None:
    household = await session.scalar(select(HouseholdRecord))
    if household is None:
        return None
    record = await session.scalar(
        select(SurfaceLayoutRecord).where(
            SurfaceLayoutRecord.household_id == household.id,
            SurfaceLayoutRecord.scope == "household-surface",
            SurfaceLayoutRecord.scope_id == "",
            SurfaceLayoutRecord.surface_class == surface_class,
            SurfaceLayoutRecord.active.is_(True),
        )
    )
    if record is None:
        return None
    return {
        "assignment_id": record.id,
        "assignment_version": record.version,
        "scope": record.scope,
        "surface_class": record.surface_class,
        "layout": record.configuration,
    }
