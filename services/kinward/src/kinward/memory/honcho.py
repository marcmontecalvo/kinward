from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Sequence

from kinward.integrations.base import IntegrationClient
from kinward.memory.contracts import ConversationMessage, MemoryHit

_ID_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_id(value: str) -> str:
    return _ID_RE.sub("_", value).strip("_")


def _items(data: Any) -> list[Any]:
    """Honcho's message create/search routes return a bare ``list[Message]`` - only
    the paginated ``/messages/list`` route wraps results in ``{"items": [...]}``.
    Accept either shape rather than assuming one.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get("items", [])
        return items if isinstance(items, list) else []
    return []


class HonchoMemoryProvider:
    """Native adapter for a locally hosted Honcho v3 API.

    Honcho remains the canonical conversational-memory authority. Kinward stores
    only provider-neutral references and does not duplicate conversation history.
    """

    name = "honcho"

    def __init__(self, *, base_url: str, transport: Any = None) -> None:
        self.client = IntegrationClient(
            name="honcho",
            base_url=base_url,
            timeout_seconds=5.0,
            transport=transport,
        )

    @staticmethod
    def workspace_id(household_id: str) -> str:
        return f"kinward_{_safe_id(household_id)}"

    @staticmethod
    def person_peer_id(person_id: str) -> str:
        return f"person_{_safe_id(person_id)}"

    @staticmethod
    def assistant_peer_id(assistant_id: str) -> str:
        return f"assistant_{_safe_id(assistant_id)}"

    @staticmethod
    def session_id(person_id: str, assistant_id: str) -> str:
        return f"session_{_safe_id(person_id)}_{_safe_id(assistant_id)}"

    async def _ensure_scope(self, household_id: str, person_id: str, assistant_id: str) -> None:
        workspace_id = self.workspace_id(household_id)
        person_peer = self.person_peer_id(person_id)
        assistant_peer = self.assistant_peer_id(assistant_id)
        session_id = self.session_id(person_id, assistant_id)

        await self.client.request("POST", "/v3/workspaces", json={"id": workspace_id})
        await self.client.request(
            "POST", f"/v3/workspaces/{workspace_id}/peers", json={"id": person_peer}
        )
        await self.client.request(
            "POST", f"/v3/workspaces/{workspace_id}/peers", json={"id": assistant_peer}
        )
        await self.client.request(
            "POST",
            f"/v3/workspaces/{workspace_id}/sessions",
            json={"id": session_id, "peers": {person_peer: {}, assistant_peer: {}}},
        )

    async def append_messages(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        messages: Sequence[ConversationMessage],
    ) -> list[str]:
        await self._ensure_scope(household_id, person_id, assistant_id)
        workspace_id = self.workspace_id(household_id)
        session_id = self.session_id(person_id, assistant_id)
        person_peer = self.person_peer_id(person_id)
        assistant_peer = self.assistant_peer_id(assistant_id)
        payload = {
            "messages": [
                {
                    "peer_id": assistant_peer if message.role == "assistant" else person_peer,
                    "content": message.content,
                    "metadata": {"role": message.role, **message.metadata},
                }
                for message in messages
            ]
        }
        data = await self.client.request_json(
            "POST",
            f"/v3/workspaces/{workspace_id}/sessions/{session_id}/messages",
            fallback=[],
            json=payload,
        )
        items = _items(data)
        return [str(item["id"]) for item in items if isinstance(item, dict) and item.get("id")]

    async def recall(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        query: str,
        limit: int = 10,
    ) -> list[MemoryHit]:
        await self._ensure_scope(household_id, person_id, assistant_id)
        workspace_id = self.workspace_id(household_id)
        session_id = self.session_id(person_id, assistant_id)
        data = await self.client.request_json(
            "POST",
            f"/v3/workspaces/{workspace_id}/sessions/{session_id}/search",
            fallback=[],
            json={"query": query, "limit": limit},
        )
        items = _items(data)
        return [self._memory_hit(item) for item in items if isinstance(item, dict)]

    async def revise(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        memory_id: str,
        content: str,
    ) -> bool:
        workspace_id = self.workspace_id(household_id)
        session_id = self.session_id(person_id, assistant_id)
        response = await self.client.request(
            "PATCH",
            f"/v3/workspaces/{workspace_id}/sessions/{session_id}/messages/{memory_id}",
            json={"content": content},
        )
        return response is not None

    async def forget(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
        memory_id: str,
    ) -> bool:
        workspace_id = self.workspace_id(household_id)
        session_id = self.session_id(person_id, assistant_id)
        response = await self.client.request(
            "DELETE",
            f"/v3/workspaces/{workspace_id}/sessions/{session_id}/messages/{memory_id}",
        )
        return response is not None

    async def export(
        self,
        *,
        household_id: str,
        person_id: str,
        assistant_id: str,
    ) -> list[MemoryHit]:
        workspace_id = self.workspace_id(household_id)
        session_id = self.session_id(person_id, assistant_id)
        data = await self.client.request_json(
            "POST",
            f"/v3/workspaces/{workspace_id}/sessions/{session_id}/messages/list",
            fallback={"items": []},
            json={},
        )
        items = _items(data)
        return [self._memory_hit(item) for item in items if isinstance(item, dict)]

    @staticmethod
    def _memory_hit(item: dict[str, Any]) -> MemoryHit:
        created_at = None
        raw_created = item.get("created_at")
        if isinstance(raw_created, str):
            try:
                created_at = datetime.fromisoformat(raw_created.replace("Z", "+00:00"))
            except ValueError:
                created_at = None
        score = item.get("score")
        return MemoryHit(
            id=str(item.get("id", "")),
            content=str(item.get("content", "")),
            score=float(score) if isinstance(score, (int, float)) else None,
            created_at=created_at,
            metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
        )
