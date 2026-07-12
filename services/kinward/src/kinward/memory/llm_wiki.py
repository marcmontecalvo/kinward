from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from urllib.parse import quote

from kinward.integrations.base import IntegrationClient
from kinward.memory.contracts import KnowledgeFact, PrivacyLevel


class LlmWikiKnowledgeProvider:
    """Native adapter for the locally hosted llm_wiki v1 facts API.

    llm_wiki remains the canonical fact authority. Kinward owns provider-neutral
    routing, privacy, provenance, and confirmation semantics.
    """

    name = "llm_wiki"

    def __init__(self, *, base_url: str, transport: Any = None) -> None:
        self.client = IntegrationClient(
            name="llm_wiki",
            base_url=base_url,
            timeout_seconds=5.0,
            transport=transport,
        )

    @staticmethod
    def workspace_id(household_id: str) -> str:
        return f"kinward_{household_id}"

    @staticmethod
    def fact_key(subject: str, predicate: str) -> str:
        return f"{subject.strip().lower()}.{predicate.strip().lower()}".replace(" ", "_")

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
        workspace_id = self.workspace_id(household_id)
        key = self.fact_key(subject, predicate)
        payload = {
            "category": "workspace.facts",
            "key": key,
            "value": {"subject": subject, "predicate": predicate, "value": value},
            "source": {"system": "kinward", "person_id": person_id, "assistant_id": assistant_id},
            "provenance": [{"reference": item} for item in provenance],
            "confidence": confidence,
            "visibility": privacy,
            "status": "proposed",
        }
        data = await self.client.request_json(
            "PUT",
            f"/v1/workspaces/{quote(workspace_id)}/facts/{quote(key)}",
            fallback={},
            json=payload,
        )
        return self._fact(data, fallback_id=key, fallback=payload)

    async def confirm_fact(self, *, fact_id: str) -> KnowledgeFact | None:
        response = await self.client.request(
            "PATCH",
            f"/v1/facts/{quote(fact_id)}",
            json={"status": "confirmed"},
        )
        if response is None:
            return None
        try:
            return self._fact(response.json(), fallback_id=fact_id)
        except ValueError:
            return None

    async def search_facts(
        self,
        *,
        household_id: str,
        person_id: str | None,
        assistant_id: str | None,
        query: str,
        limit: int = 10,
    ) -> list[KnowledgeFact]:
        workspace_id = self.workspace_id(household_id)
        data = await self.client.request_json(
            "GET",
            f"/v1/workspaces/{quote(workspace_id)}/facts",
            fallback={"items": []},
            params={
                "q": query,
                "limit": limit,
                "person_id": person_id,
                "assistant_id": assistant_id,
            },
        )
        items = data.get("items", data) if isinstance(data, dict) else data
        return [self._fact(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []

    async def revise_fact(
        self,
        *,
        fact_id: str,
        value: Any,
        provenance: Sequence[str],
        confidence: float,
    ) -> KnowledgeFact | None:
        response = await self.client.request(
            "PATCH",
            f"/v1/facts/{quote(fact_id)}",
            json={
                "value": value,
                "provenance": [{"reference": item} for item in provenance],
                "confidence": confidence,
            },
        )
        if response is None:
            return None
        try:
            return self._fact(response.json(), fallback_id=fact_id)
        except ValueError:
            return None

    async def retire_fact(self, *, fact_id: str) -> bool:
        response = await self.client.request(
            "PATCH",
            f"/v1/facts/{quote(fact_id)}",
            json={"status": "retired"},
        )
        return response is not None

    async def provenance(self, *, fact_id: str) -> list[str]:
        data = await self.client.request_json(
            "GET",
            f"/v1/facts/{quote(fact_id)}/history",
            fallback={"items": []},
        )
        items = data.get("items", data) if isinstance(data, dict) else data
        references: list[str] = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                for provenance in item.get("provenance", []):
                    if isinstance(provenance, dict) and provenance.get("reference"):
                        references.append(str(provenance["reference"]))
        return list(dict.fromkeys(references))

    @staticmethod
    def _fact(
        data: dict[str, Any],
        *,
        fallback_id: str = "",
        fallback: dict[str, Any] | None = None,
    ) -> KnowledgeFact:
        source = data or fallback or {}
        wrapped_value = source.get("value", {})
        if not isinstance(wrapped_value, dict):
            wrapped_value = {"value": wrapped_value}
        raw_provenance = source.get("provenance", [])
        provenance = tuple(
            str(item.get("reference"))
            for item in raw_provenance
            if isinstance(item, dict) and item.get("reference")
        )
        updated_at = None
        raw_updated = source.get("updated_at")
        if isinstance(raw_updated, str):
            try:
                updated_at = datetime.fromisoformat(raw_updated.replace("Z", "+00:00"))
            except ValueError:
                updated_at = None
        status = str(source.get("status", "proposed"))
        if status not in {"proposed", "confirmed", "retired"}:
            status = "proposed"
        privacy = str(source.get("visibility", "personal"))
        if privacy not in {"household", "personal", "sensitive"}:
            privacy = "personal"
        return KnowledgeFact(
            id=str(source.get("id") or source.get("key") or fallback_id),
            subject=str(wrapped_value.get("subject", "")),
            predicate=str(wrapped_value.get("predicate", "")),
            value=wrapped_value.get("value"),
            status=status,  # type: ignore[arg-type]
            privacy=privacy,  # type: ignore[arg-type]
            provenance=provenance,
            confidence=float(source.get("confidence") or 0.0),
            updated_at=updated_at,
            metadata={"category": source.get("category")},
        )
