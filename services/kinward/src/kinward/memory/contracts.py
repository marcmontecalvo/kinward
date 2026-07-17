from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, Sequence

MemoryRole = Literal["user", "assistant", "system"]
KnowledgeStatus = Literal["proposed", "confirmed", "retired"]
PrivacyLevel = Literal["household", "personal", "sensitive"]


@dataclass(frozen=True)
class ConversationMessage:
    role: MemoryRole
    content: str
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryHit:
    id: str
    content: str
    score: float | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeFact:
    id: str
    subject: str
    predicate: str
    value: Any
    status: KnowledgeStatus
    privacy: PrivacyLevel
    provenance: Sequence[str] = field(default_factory=tuple)
    confidence: float = 1.0
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationalMemoryProvider(Protocol):
    name: str

    async def append_messages(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        messages: Sequence[ConversationMessage],
    ) -> list[str]: ...

    async def recall(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        query: str,
        limit: int = 10,
    ) -> list[MemoryHit]: ...

    async def revise(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        memory_id: str,
        content: str,
    ) -> bool: ...

    async def forget(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        memory_id: str,
    ) -> bool: ...

    async def export(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
    ) -> list[MemoryHit]: ...


class KnowledgeStoreProvider(Protocol):
    name: str

    async def propose_fact(
        self,
        *,
        household_id: str,
        person_id: str | None,
        assistant_id: str | None,
        subject: str,
        predicate: str,
        value: Any,
        privacy: PrivacyLevel,
        provenance: Sequence[str],
        confidence: float,
    ) -> KnowledgeFact: ...

    async def confirm_fact(self, *, fact_id: str) -> KnowledgeFact | None: ...

    async def search_facts(
        self,
        *,
        household_id: str,
        person_id: str | None,
        assistant_id: str | None,
        query: str,
        limit: int = 10,
    ) -> list[KnowledgeFact]: ...

    async def revise_fact(
        self,
        *,
        fact_id: str,
        value: Any,
        provenance: Sequence[str],
        confidence: float,
    ) -> KnowledgeFact | None: ...

    async def retire_fact(self, *, fact_id: str) -> bool: ...

    async def reclassify_fact(self, *, fact_id: str, privacy: PrivacyLevel) -> KnowledgeFact | None: ...

    async def provenance(self, *, fact_id: str) -> list[str]: ...
