import httpx
import pytest

from kinward.integrations.base import IntegrationClient
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.integrations.memory import KnowledgeClient, MemoryClient


@pytest.mark.asyncio
async def test_disabled_integrations_return_safe_fallbacks() -> None:
    assert await MemoryClient(base_url=None).recall(
        person_id="person", assistant_id="assistant", query="paint color"
    ) == []
    assert await KnowledgeClient(base_url=None).search(query="manual") == []
    assert await HomeAssistantClient(base_url=None, token=None).states() == []


@pytest.mark.asyncio
async def test_integration_client_returns_json_on_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = IntegrationClient(
        name="test",
        base_url="https://example.invalid",
        transport=httpx.MockTransport(handler),
    )

    assert await client.request_json("GET", "/health", fallback={}) == {"ok": True}
    assert client.status().state == "available"


@pytest.mark.asyncio
async def test_integration_client_degrades_and_opens_circuit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    client = IntegrationClient(
        name="test",
        base_url="https://example.invalid",
        failure_threshold=2,
        transport=httpx.MockTransport(handler),
    )

    assert await client.request_json("GET", "/health", fallback={"ok": False}) == {"ok": False}
    assert await client.request_json("GET", "/health", fallback={"ok": False}) == {"ok": False}
    assert client.circuit_open
    assert client.status().state == "degraded"
