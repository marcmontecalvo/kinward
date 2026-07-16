from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import secrets
from typing import Any, Protocol

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import (
    ActivityRecord,
    AssistantRecord,
    BootstrapAttemptRecord,
    HouseholdRecord,
    OutboxMessageRecord,
    PetRecord,
    SetupCapabilityRecord,
)
from kinward.domain.assistant_ownership import validate_owner_count


class BootstrapUnitOfWork(Protocol):
    session: AsyncSession

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@dataclass
class SqlAlchemyBootstrapUnitOfWork:
    session: AsyncSession

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class BootstrapError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class SelectedPet:
    display_name: str
    species: str
    shared_facts: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapCommand:
    household_name: str
    fallback_assistant_name: str
    pets: tuple[SelectedPet, ...]
    idempotency_key: str
    setup_authorization: str

    def fingerprint(self) -> str:
        payload = {
            "household_name": self.household_name.strip(),
            "fallback_assistant_name": self.fallback_assistant_name.strip(),
            "pets": [
                {"display_name": pet.display_name, "species": pet.species, "shared_facts": pet.shared_facts}
                for pet in self.pets
            ],
        }
        return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def capability_hash(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def enforce_bootstrap_policy(command: BootstrapCommand) -> None:
    fallback_valid, _ = validate_owner_count(assistant_type="shared-fallback", owner_count=0)
    if not fallback_valid:
        raise BootstrapError("ownership_invariant", "Assistant ownership policy rejected setup.")


async def execute_bootstrap(
    unit_of_work: BootstrapUnitOfWork,
    command: BootstrapCommand,
    *,
    configured_authorization: str,
    authorization_ttl_seconds: int,
) -> dict[str, Any]:
    session = unit_of_work.session
    enforce_bootstrap_policy(command)
    bind = session.get_bind()
    if bind.dialect.name == "sqlite":
        await session.execute(text("BEGIN IMMEDIATE"))
    fingerprint = command.fingerprint()
    replay = await session.scalar(
        select(BootstrapAttemptRecord).where(
            BootstrapAttemptRecord.idempotency_key == command.idempotency_key
        )
    )
    if replay is not None:
        if replay.request_fingerprint != fingerprint:
            raise BootstrapError("idempotency_conflict", "That setup request identity was already used.")
        return dict(replay.result)

    if await session.scalar(select(func.count()).select_from(HouseholdRecord)):
        raise BootstrapError("already_configured", "This Kinward deployment already has a household.")
    if not configured_authorization or not secrets.compare_digest(
        command.setup_authorization, configured_authorization
    ):
        raise BootstrapError("setup_authorization_invalid", "Setup authorization is invalid or expired.")

    now = datetime.now(timezone.utc)
    verifier = capability_hash(command.setup_authorization)
    capability = await session.scalar(
        select(SetupCapabilityRecord).where(SetupCapabilityRecord.verifier_hash == verifier)
    )
    if capability is None:
        capability = SetupCapabilityRecord(
            verifier_hash=verifier,
            expires_at=now + timedelta(seconds=authorization_ttl_seconds),
        )
        session.add(capability)
        await session.flush()
    expires_at = capability.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if capability.consumed_at is not None or expires_at <= now:
        raise BootstrapError("setup_authorization_invalid", "Setup authorization is invalid or expired.")

    household = HouseholdRecord(name=command.household_name.strip())
    session.add(household)
    try:
        await session.flush()
    except IntegrityError as error:
        raise BootstrapError(
            "bootstrap_conflict",
            "Setup could not be committed safely. Retry with the same request identity.",
            retryable=True,
        ) from error
    fallback = AssistantRecord(
        household_id=household.id,
        owner_person_id=None,
        name=command.fallback_assistant_name.strip(),
        kind="household-fallback",
        classification="household-shared",
    )
    session.add(fallback)
    for pet in command.pets:
        session.add(
            PetRecord(
                household_id=household.id,
                display_name=pet.display_name.strip(),
                species=pet.species.strip(),
                shared_facts=list(pet.shared_facts),
            )
        )
    await session.flush()
    result = {
        "household_id": household.id,
        "fallback_assistant_id": fallback.id,
    }
    session.add_all(
        [
            BootstrapAttemptRecord(
                idempotency_key=command.idempotency_key,
                request_fingerprint=fingerprint,
                result=result,
            ),
            ActivityRecord(
                household_id=household.id,
                person_id=None,
                assistant_id=fallback.id,
                summary="Household setup completed",
                outcome="completed",
                detail={"classification": "system-operational"},
            ),
            OutboxMessageRecord(
                topic="household.bootstrap.completed",
                payload={"household_id": household.id, "classification": "system-operational"},
            ),
        ]
    )
    capability.consumed_at = now
    await unit_of_work.commit()
    return result
