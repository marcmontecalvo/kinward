from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.memory.contracts import KnowledgeStoreProvider, PrivacyLevel
from kinward.persistence.models import KnowledgeFactRecord

PENDING_OBSERVATION_EXPIRY_DAYS = 30

_TERMINAL_STATES = frozenset({"rejected", "expired", "deleted"})


@dataclass(frozen=True)
class FactNotFound:
    """No such fact, or it isn't owned by the resolved person - fail closed either way."""


@dataclass(frozen=True)
class NotPending:
    """The fact isn't a pending-inferred-observation - confirm/reject only apply there."""


@dataclass(frozen=True)
class NotConfirmed:
    """The fact isn't a confirmed-durable-fact - correction/deletion only apply there."""


@dataclass(frozen=True)
class ProviderUnavailable:
    """No knowledge provider is configured - cannot create, confirm, or reach a body."""


@dataclass(frozen=True)
class Suppressed:
    """Identical evidence was already rejected once - recurrence suppressed, no new observation."""


@dataclass(frozen=True)
class Disposed:
    fact_id: str


def _recurrence_key(
    *, subject: str, predicate: str, source_system: str, source_version: str | None
) -> str:
    raw = "|".join(
        part.strip().lower()
        for part in (subject, predicate, source_system, source_version or "")
    )
    return hashlib.sha256(raw.encode()).hexdigest()


async def propose_observation(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    household_id: str,
    owner_person_id: str,
    assistant_id: str | None,
    subject: str,
    predicate: str,
    value: Any,
    privacy: str,
    source_system: str,
    source_version: str | None = None,
    confidence: float = 1.0,
) -> KnowledgeFactRecord | ProviderUnavailable | Suppressed:
    """Create a pending inferred observation (AD-25): inspection-only until confirmed.

    Identical evidence (same subject/predicate/source/version) that was already
    rejected once is suppressed rather than re-proposed - "recurrence suppression"
    from Story 4.3's acceptance criteria.
    """
    if provider.name == "none":
        return ProviderUnavailable()

    key = _recurrence_key(
        subject=subject, predicate=predicate, source_system=source_system, source_version=source_version
    )
    already_rejected = await session.scalar(
        select(KnowledgeFactRecord).where(
            KnowledgeFactRecord.household_id == household_id,
            KnowledgeFactRecord.recurrence_key == key,
            KnowledgeFactRecord.knowledge_state == "rejected",
        )
    )
    if already_rejected is not None:
        return Suppressed()

    fact = await provider.propose_fact(
        household_id=household_id,
        person_id=owner_person_id,
        assistant_id=assistant_id,
        subject=subject,
        predicate=predicate,
        value=value,
        privacy=privacy,  # type: ignore[arg-type]
        provenance=[source_system],
        confidence=confidence,
    )

    now = datetime.now(UTC)
    record = KnowledgeFactRecord(
        household_id=household_id,
        owner_person_id=owner_person_id,
        subject=subject.strip(),
        predicate=predicate.strip(),
        value=value,
        privacy=privacy,
        source_system=source_system.strip(),
        source_version=source_version,
        confidence=confidence,
        recurrence_key=key,
        knowledge_state="pending",
        external_fact_id=fact.id,
        created_at=now,
        expires_at=now + timedelta(days=PENDING_OBSERVATION_EXPIRY_DAYS),
    )
    session.add(record)
    await session.flush()
    return record


async def _find_owned(
    session: AsyncSession, *, person_id: str, fact_id: str
) -> KnowledgeFactRecord | None:
    fact = await session.get(KnowledgeFactRecord, fact_id)
    if fact is None or fact.owner_person_id != person_id:
        return None
    return fact


async def list_pending_observations(
    session: AsyncSession, *, ha_user_id: str
) -> list[KnowledgeFactRecord] | Unmapped:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    rows = await session.scalars(
        select(KnowledgeFactRecord)
        .where(
            KnowledgeFactRecord.owner_person_id == person.id,
            KnowledgeFactRecord.knowledge_state == "pending",
        )
        .order_by(KnowledgeFactRecord.created_at)
    )
    return list(rows)


async def list_confirmed_facts(
    session: AsyncSession, *, ha_user_id: str
) -> list[KnowledgeFactRecord] | Unmapped:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    rows = await session.scalars(
        select(KnowledgeFactRecord)
        .where(
            KnowledgeFactRecord.owner_person_id == person.id,
            KnowledgeFactRecord.knowledge_state == "confirmed",
        )
        .order_by(KnowledgeFactRecord.subject, KnowledgeFactRecord.predicate)
    )
    return list(rows)


async def confirm_observation(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    ha_user_id: str,
    fact_id: str,
) -> KnowledgeFactRecord | FactNotFound | NotPending | Unmapped | ProviderUnavailable:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    record = await _find_owned(session, person_id=person.id, fact_id=fact_id)
    if record is None:
        return FactNotFound()
    if record.knowledge_state != "pending":
        return NotPending()
    if provider.name == "none":
        return ProviderUnavailable()

    if record.external_fact_id and await provider.confirm_fact(fact_id=record.external_fact_id) is None:
        return ProviderUnavailable()
    record.knowledge_state = "confirmed"
    record.confirmed_at = datetime.now(UTC)
    record.expires_at = None
    record.record_version += 1
    await session.flush()
    return record


async def _dispose(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    record: KnowledgeFactRecord,
    *,
    new_state: str,
) -> None:
    """Remove a fact's body and cascade AD-25's dependents invalidation.

    If the provider can't confirm the body is gone, the reference is marked
    ``deletion_pending`` rather than silently treated as fully removed - the
    provider-side deletion still needs to be pursued/retried later.
    """
    removed = True
    if record.external_fact_id and provider.name != "none":
        removed = await provider.retire_fact(fact_id=record.external_fact_id)

    record.knowledge_state = new_state
    record.deletion_status = "none" if removed else "deletion_pending"
    record.disposed_at = datetime.now(UTC)
    record.expires_at = None
    record.record_version += 1
    await session.flush()
    await _invalidate_dependents(session, provider, record.id)


async def _invalidate_dependents(
    session: AsyncSession, provider: KnowledgeStoreProvider, fact_id: str
) -> None:
    """Recursively dispose any fact that named ``fact_id`` in its ``depends_on``.

    Nothing currently populates ``depends_on`` (no fact is yet derived from
    another), so this is structurally ready but not yet exercised in
    production - it exists so a future fact-derivation feature doesn't need to
    reinvent AD-25's invalidation rule.
    """
    candidates = await session.scalars(
        select(KnowledgeFactRecord).where(
            KnowledgeFactRecord.knowledge_state.notin_(_TERMINAL_STATES)
        )
    )
    for dependent in candidates:
        if fact_id in dependent.depends_on:
            await _dispose(session, provider, dependent, new_state="expired")


async def reject_observation(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    ha_user_id: str,
    fact_id: str,
) -> Disposed | FactNotFound | NotPending | Unmapped:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    record = await _find_owned(session, person_id=person.id, fact_id=fact_id)
    if record is None:
        return FactNotFound()
    if record.knowledge_state != "pending":
        return NotPending()
    await _dispose(session, provider, record, new_state="rejected")
    return Disposed(fact_id=fact_id)


async def expire_due_observations(
    session: AsyncSession, provider: KnowledgeStoreProvider, *, now: datetime | None = None
) -> int:
    """Dispose every pending observation past its fixed 30-day expiry (AD-25)."""
    cutoff = now or datetime.now(UTC)
    due = await session.scalars(
        select(KnowledgeFactRecord).where(
            KnowledgeFactRecord.knowledge_state == "pending",
            KnowledgeFactRecord.expires_at <= cutoff,
        )
    )
    count = 0
    for record in due:
        await _dispose(session, provider, record, new_state="expired")
        count += 1
    return count


async def correct_fact(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    ha_user_id: str,
    fact_id: str,
    value: Any,
    confidence: float | None = None,
) -> KnowledgeFactRecord | FactNotFound | NotConfirmed | Unmapped | ProviderUnavailable:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    record = await _find_owned(session, person_id=person.id, fact_id=fact_id)
    if record is None:
        return FactNotFound()
    if record.knowledge_state != "confirmed":
        return NotConfirmed()
    if provider.name == "none":
        return ProviderUnavailable()

    if record.external_fact_id:
        revised = await provider.revise_fact(
            fact_id=record.external_fact_id,
            value=value,
            provenance=[record.source_system],
            confidence=confidence if confidence is not None else record.confidence,
        )
        if revised is None:
            return ProviderUnavailable()
    record.value = value
    if confidence is not None:
        record.confidence = confidence
    record.record_version += 1
    await session.flush()
    return record


async def reclassify_fact(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    ha_user_id: str,
    fact_id: str,
    privacy: PrivacyLevel,
) -> KnowledgeFactRecord | FactNotFound | NotConfirmed | Unmapped | ProviderUnavailable:
    """Change a confirmed fact's sharing class (personal/household/sensitive).

    Owner-unilateral in either direction, same trust level as ``correct_fact``:
    nothing today reads ``privacy`` to gate rendering or access, so narrowing and
    widening carry the same risk as any other self-owned correction.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    record = await _find_owned(session, person_id=person.id, fact_id=fact_id)
    if record is None:
        return FactNotFound()
    if record.knowledge_state != "confirmed":
        return NotConfirmed()
    if provider.name == "none":
        return ProviderUnavailable()

    if record.external_fact_id:
        reclassified = await provider.reclassify_fact(fact_id=record.external_fact_id, privacy=privacy)
        if reclassified is None:
            return ProviderUnavailable()
    record.privacy = privacy
    record.record_version += 1
    await session.flush()
    return record


async def delete_fact(
    session: AsyncSession,
    provider: KnowledgeStoreProvider,
    *,
    ha_user_id: str,
    fact_id: str,
) -> Disposed | FactNotFound | NotConfirmed | Unmapped:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    record = await _find_owned(session, person_id=person.id, fact_id=fact_id)
    if record is None:
        return FactNotFound()
    if record.knowledge_state != "confirmed":
        return NotConfirmed()
    await _dispose(session, provider, record, new_state="deleted")
    return Disposed(fact_id=fact_id)
