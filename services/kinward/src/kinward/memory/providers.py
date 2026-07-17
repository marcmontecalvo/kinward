from __future__ import annotations

from typing import Any, Sequence

from kinward.memory.contracts import KnowledgeFact, MemoryHit, PrivacyLevel


class NullConversationalMemoryProvider:
    name = "none"

    async def append_messages(self, **_: Any) -> list[str]:
        return []

    async def recall(self, **_: Any) -> list[MemoryHit]:
        return []

    async def revise(self, **_: Any) -> bool:
        return False

    async def forget(self, **_: Any) -> bool:
        return False

    async def export(self, **_: Any) -> list[MemoryHit]:
        return []


class NullKnowledgeStoreProvider:
    name = "none"

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
    ) -> KnowledgeFact:
        raise RuntimeError("No knowledge provider is configured.")

    async def confirm_fact(self, *, fact_id: str) -> KnowledgeFact | None:
        return None

    async def search_facts(self, **_: Any) -> list[KnowledgeFact]:
        return []

    async def revise_fact(self, **_: Any) -> KnowledgeFact | None:
        return None

    async def retire_fact(self, *, fact_id: str) -> bool:
        return False

    async def reclassify_fact(self, *, fact_id: str, privacy: PrivacyLevel) -> KnowledgeFact | None:
        return None

    async def provenance(self, *, fact_id: str) -> list[str]:
        return []
