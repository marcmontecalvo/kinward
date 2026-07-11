from __future__ import annotations

from typing import Any

from kinward.integrations.base import IntegrationClient


class HomeAssistantClient:
    def __init__(self, *, base_url: str | None, token: str | None) -> None:
        self.token = token
        self.client = IntegrationClient(name="home-assistant", base_url=base_url)

    @property
    def enabled(self) -> bool:
        return self.client.enabled and bool(self.token)

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    async def states(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        result = await self.client.request_json(
            "GET",
            "/api/states",
            fallback=[],
            headers=self._headers(),
        )
        return result if isinstance(result, list) else []

    async def call_service(
        self,
        *,
        domain: str,
        service: str,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        result = await self.client.request_json(
            "POST",
            f"/api/services/{domain}/{service}",
            fallback=[],
            headers=self._headers(),
            json=data,
        )
        return result if isinstance(result, list) else []
