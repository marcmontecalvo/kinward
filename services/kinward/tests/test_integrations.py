import httpx
import pytest

from kinward.integrations.base import IntegrationClient
from kinward.integrations.home_assistant import HomeAssistantClient


@pytest.mark.asyncio
async def test_unconfigured_home_assistant_returns_a_safe_fallback() -> None:
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

    assert client.status().state == "unavailable"
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


@pytest.mark.asyncio
async def test_invalid_json_counts_toward_the_circuit_threshold() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = IntegrationClient(
        name="test",
        base_url="https://example.invalid",
        failure_threshold=2,
        transport=httpx.MockTransport(handler),
    )

    assert await client.request_json("GET", "/health", fallback={}) == {}
    assert not client.circuit_open
    assert await client.request_json("GET", "/health", fallback={}) == {}
    assert client.circuit_open
    assert client.status().state == "degraded"
