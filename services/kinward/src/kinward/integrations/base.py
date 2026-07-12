from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx

IntegrationState = Literal["available", "degraded", "disabled"]


@dataclass(frozen=True)
class IntegrationStatus:
    name: str
    state: IntegrationState
    detail: str | None = None


class IntegrationClient:
    """Small resilient HTTP client for optional household integrations."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str | None,
        timeout_seconds: float = 2.0,
        failure_threshold: int = 3,
        recovery_seconds: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout_seconds = timeout_seconds
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.transport = transport
        self.consecutive_failures = 0
        self.opened_at: float | None = None
        self.last_error: str | None = None

    @property
    def enabled(self) -> bool:
        return self.base_url is not None

    @property
    def circuit_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            self.opened_at = None
            return False
        return True

    def status(self) -> IntegrationStatus:
        if not self.enabled:
            return IntegrationStatus(self.name, "disabled", "Integration is not configured.")
        if self.circuit_open or self.last_error:
            return IntegrationStatus(self.name, "degraded", self.last_error)
        return IntegrationStatus(self.name, "available")

    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response | None:
        if not self.enabled or self.circuit_open:
            return None

        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                )
                response.raise_for_status()
            self.consecutive_failures = 0
            self.last_error = None
            return response
        except httpx.HTTPError as exc:
            self.consecutive_failures += 1
            self.last_error = exc.__class__.__name__
            if self.consecutive_failures >= self.failure_threshold:
                self.opened_at = time.monotonic()
            return None

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        fallback: Any,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = await self.request(
            method,
            path,
            headers=headers,
            json=json,
            params=params,
        )
        if response is None:
            return fallback
        try:
            return response.json()
        except ValueError:
            self.last_error = "InvalidJSON"
            return fallback
