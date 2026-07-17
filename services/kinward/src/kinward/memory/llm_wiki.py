from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence, cast
from urllib.parse import quote

from kinward.integrations.base import IntegrationClient
from kinward.memory.contracts import KnowledgeFact, KnowledgeStatus, PrivacyLevel


class LlmWikiKnowledgeProvider:
    name = "llm_wiki"

    def __init__(self, *, base_url: str, transport: Any = None) -> None:
        self.client = IntegrationClient(name="llm_wiki", base_url=base_url, timeout_seconds=5.0, transport=transport)

    @staticmethod
    def workspace_id(household_id: str) -> str:
        return f"kinward_{household_id}"

    @staticmethod
    def fact_key(subject: str, predicate: str) -> str:
        return f"{subject.strip().lower()}.{predicate.strip().lower()}".replace(" ", "_")

    @staticmethod
    def fact_id(workspace_id: str, key: str) -> str:
        return f"{workspace_id}::{key}"

    @staticmethod
    def parse_fact_id(fact_id: str) -> tuple[str, str]:
        workspace_id, separator, key = fact_id.partition("::")
        if not separator or not workspace_id or not key:
            raise ValueError("Fact ID must contain workspace and key.")
        return workspace_id, key

    async def propose_fact(self, *, household_id: str, person_id: str | None, assistant_id: str | None, subject: str, predicate: str, value: Any, privacy: PrivacyLevel, provenance: Sequence[str], confidence: float) -> KnowledgeFact:
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
        data = await self.client.request_json("PUT", f"/v1/workspaces/{quote(workspace_id)}/facts/{quote(key)}", fallback={}, json=payload)
        return self._fact(data, fallback_id=self.fact_id(workspace_id, key), fallback=payload)

    async def confirm_fact(self, *, fact_id: str) -> KnowledgeFact | None:
        return await self._patch_fact(fact_id, {"status": "confirmed"})

    async def search_facts(self, *, household_id: str, person_id: str | None, assistant_id: str | None, query: str, limit: int = 10) -> list[KnowledgeFact]:
        workspace_id = self.workspace_id(household_id)
        data = await self.client.request_json("GET", f"/v1/workspaces/{quote(workspace_id)}/facts", fallback={"items": []}, params={"q": query, "limit": limit, "person_id": person_id, "assistant_id": assistant_id})
        items = data.get("items", data) if isinstance(data, dict) else data
        return [self._fact(item, fallback_id=self.fact_id(workspace_id, str(item.get("key", "")))) for item in items if isinstance(item, dict)] if isinstance(items, list) else []

    async def revise_fact(self, *, fact_id: str, value: Any, provenance: Sequence[str], confidence: float) -> KnowledgeFact | None:
        return await self._patch_fact(fact_id, {"value": value, "provenance": [{"reference": item} for item in provenance], "confidence": confidence})

    async def retire_fact(self, *, fact_id: str) -> bool:
        return await self._patch_fact(fact_id, {"status": "retired"}) is not None

    async def reclassify_fact(self, *, fact_id: str, privacy: PrivacyLevel) -> KnowledgeFact | None:
        return await self._patch_fact(fact_id, {"visibility": privacy})

    async def provenance(self, *, fact_id: str) -> list[str]:
        workspace_id, key = self.parse_fact_id(fact_id)
        data = await self.client.request_json("GET", f"/v1/workspaces/{quote(workspace_id)}/facts/{quote(key)}/history", fallback={"items": []})
        items = data.get("items", data) if isinstance(data, dict) else data
        references: list[str] = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for entry in item.get("provenance", []):
                        if isinstance(entry, dict) and entry.get("reference"):
                            references.append(str(entry["reference"]))
        return list(dict.fromkeys(references))

    async def _patch_fact(self, fact_id: str, payload: dict[str, Any]) -> KnowledgeFact | None:
        workspace_id, key = self.parse_fact_id(fact_id)
        current = await self.client.request_json("GET", f"/v1/workspaces/{quote(workspace_id)}/facts/{quote(key)}", fallback={})
        if not isinstance(current, dict) or not current:
            return None
        merged = {**current, **payload, "key": key}
        data = await self.client.request_json("PUT", f"/v1/workspaces/{quote(workspace_id)}/facts/{quote(key)}", fallback={}, json=merged)
        return self._fact(data, fallback_id=fact_id, fallback=merged) if isinstance(data, dict) else None

    @staticmethod
    def _fact(data: dict[str, Any], *, fallback_id: str = "", fallback: dict[str, Any] | None = None) -> KnowledgeFact:
        source = data or fallback or {}
        wrapped_value = source.get("value", {})
        if not isinstance(wrapped_value, dict):
            wrapped_value = {"value": wrapped_value}
        raw_provenance = source.get("provenance", [])
        provenance = tuple(str(item.get("reference")) for item in raw_provenance if isinstance(item, dict) and item.get("reference"))
        updated_at = None
        if isinstance(source.get("updated_at"), str):
            try:
                updated_at = datetime.fromisoformat(str(source["updated_at"]).replace("Z", "+00:00"))
            except ValueError:
                pass
        status_value = str(source.get("status", "proposed"))
        privacy_value = str(source.get("visibility", "personal"))
        status = cast(KnowledgeStatus, status_value if status_value in {"proposed", "confirmed", "retired"} else "proposed")
        privacy = cast(PrivacyLevel, privacy_value if privacy_value in {"household", "personal", "sensitive"} else "personal")
        return KnowledgeFact(id=str(source.get("id") or fallback_id), subject=str(wrapped_value.get("subject", "")), predicate=str(wrapped_value.get("predicate", "")), value=wrapped_value.get("value"), status=status, privacy=privacy, provenance=provenance, confidence=float(source.get("confidence") or 0.0), updated_at=updated_at, metadata={"category": source.get("category"), "key": source.get("key")})
