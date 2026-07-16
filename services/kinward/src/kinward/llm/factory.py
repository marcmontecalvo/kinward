from __future__ import annotations

from kinward.llm.anthropic import AnthropicModelProvider
from kinward.llm.contracts import ModelProvider
from kinward.llm.openai_compatible import OpenAiCompatibleModelProvider
from kinward.llm.providers import NullModelProvider

_OPENAI_SHAPED_PROVIDERS = {"openai", "openai-compatible"}


def model_provider(
    *, provider: str, base_url: str | None, model_name: str | None, api_key: str | None
) -> ModelProvider:
    if not base_url or not model_name:
        return NullModelProvider()
    if provider in _OPENAI_SHAPED_PROVIDERS:
        return OpenAiCompatibleModelProvider(base_url=base_url, model_name=model_name, api_key=api_key)
    if provider == "anthropic":
        return AnthropicModelProvider(base_url=base_url, model_name=model_name, api_key=api_key)
    return NullModelProvider()
