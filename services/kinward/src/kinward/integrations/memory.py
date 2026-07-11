from __future__ import annotations

from typing import Any

from kinward.integrations.base import IntegrationClient


class MemoryClient:
    def __init__(self, *, base_url: str | None) -> None:
        self.client = IntegrationClient(name="memory", base_url=base_url)

    async def recall(self, *, person_id: str, assistant_id: str, query: str) -> list[dict[str, Any]]:
        result = await self.client.request_json(
            "POST",
            "/recall",
            fallback=[],
            json={"person_id": person_id, "assistant_id": assistant_id, "query": query},
        )
        return result if isinstance(result, list) else []

    async def remember(
        self,
        *,
        person_id: str,
        assistant_id: str,
        content: str,
        sensitivity: str = "personal",
    ) -> bool:
        result = await self.client.request_json(
            "POST",
            "/memories",
            fallback={"stored": False},
            json={
                "person_id": person_id,
                "assistant_id": assistant_id,
                "content": content,
                "sensitivity": sensitivity,
            },
        )
        return bool(result.get("stored")) if isinstance(result, dict) else False


class KnowledgeClient:
    def __init__(self, *, base_url: str | None) -> None:
        self.client = IntegrationClient(name="knowledge", base_url=base_url)

    async def search(self, *, query: str, limit: int = 5) -> list[dict[str, Any]]:
        result = await self.client.request_json(
            "POST",
            "/search",
            fallback=[],
            json={"query": query, "limit": limit},
        )
        return result if isinstance(result, list) else []
