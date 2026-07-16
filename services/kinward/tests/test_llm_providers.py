from __future__ import annotations

import httpx

from kinward.llm.anthropic import AnthropicModelProvider
from kinward.llm.contracts import ModelMessage
from kinward.llm.factory import model_provider
from kinward.llm.openai_compatible import OpenAiCompatibleModelProvider
from kinward.llm.providers import MODEL_UNAVAILABLE_RESPONSE, NO_MODEL_RESPONSE, NullModelProvider


async def test_null_provider_never_fabricates_a_reply() -> None:
    provider = NullModelProvider()
    reply = await provider.generate_reply(
        system_prompt="anything", messages=[ModelMessage(role="user", content="hi")]
    )
    assert reply.content == NO_MODEL_RESPONSE


async def test_factory_falls_back_to_none_without_a_base_url_or_model_name() -> None:
    assert model_provider(provider="openai", base_url=None, model_name="gpt-5", api_key=None).name == "none"
    assert model_provider(provider="openai", base_url="https://api.openai.com/v1", model_name=None, api_key=None).name == "none"
    assert model_provider(provider="unknown", base_url="https://x.invalid", model_name="m", api_key=None).name == "none"


async def test_factory_dispatches_openai_and_anthropic_shapes() -> None:
    assert (
        model_provider(
            provider="openai", base_url="https://api.openai.com/v1", model_name="gpt-5", api_key="k"
        ).name
        == "openai"
    )
    assert (
        model_provider(
            provider="openai-compatible", base_url="http://ollama.local:11434/v1", model_name="llama3", api_key=None
        ).name
        == "openai"
    )
    assert (
        model_provider(
            provider="anthropic", base_url="https://api.anthropic.com/v1", model_name="claude", api_key="k"
        ).name
        == "anthropic"
    )


async def test_openai_compatible_provider_sends_bearer_auth_and_parses_reply() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("Authorization")
        seen["body"] = request.content
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "Hello there"}}]}
        )

    provider = OpenAiCompatibleModelProvider(
        base_url="http://model.invalid/v1",
        model_name="gpt-5",
        api_key="secret-key",
        transport=httpx.MockTransport(handler),
    )
    reply = await provider.generate_reply(
        system_prompt="You are helpful.", messages=[ModelMessage(role="user", content="hi")]
    )
    assert reply.content == "Hello there"
    assert seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer secret-key"


async def test_openai_compatible_provider_degrades_truthfully_on_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    provider = OpenAiCompatibleModelProvider(
        base_url="http://model.invalid/v1",
        model_name="gpt-5",
        api_key=None,
        transport=httpx.MockTransport(handler),
    )
    reply = await provider.generate_reply(system_prompt="x", messages=[])
    assert reply.content == MODEL_UNAVAILABLE_RESPONSE


async def test_anthropic_provider_sends_api_key_header_and_parses_reply() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["api_key"] = request.headers.get("x-api-key")
        seen["version"] = request.headers.get("anthropic-version")
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Hi from Claude"}]})

    provider = AnthropicModelProvider(
        base_url="https://api.anthropic.com/v1",
        model_name="claude-sonnet",
        api_key="ant-key",
        transport=httpx.MockTransport(handler),
    )
    reply = await provider.generate_reply(
        system_prompt="You are helpful.", messages=[ModelMessage(role="user", content="hi")]
    )
    assert reply.content == "Hi from Claude"
    assert seen["path"] == "/v1/messages"
    assert seen["api_key"] == "ant-key"
    assert seen["version"] == "2023-06-01"


async def test_anthropic_provider_degrades_truthfully_on_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    provider = AnthropicModelProvider(
        base_url="https://api.anthropic.com/v1",
        model_name="claude-sonnet",
        api_key="bad-key",
        transport=httpx.MockTransport(handler),
    )
    reply = await provider.generate_reply(system_prompt="x", messages=[])
    assert reply.content == MODEL_UNAVAILABLE_RESPONSE
