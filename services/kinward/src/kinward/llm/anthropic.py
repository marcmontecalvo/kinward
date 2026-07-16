from __future__ import annotations

from typing import Any, Sequence

from kinward.integrations.base import IntegrationClient
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.llm.providers import MODEL_UNAVAILABLE_RESPONSE

ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024


class AnthropicModelProvider:
    """Adapter for Anthropic's Messages API.

    ``base_url`` is the API root (e.g. ``https://api.anthropic.com/v1``) -
    ``/messages`` is appended to it.
    """

    name = "anthropic"

    def __init__(self, *, base_url: str, model_name: str, api_key: str | None, transport: Any = None) -> None:
        self.model_name = model_name
        self.client = IntegrationClient(
            name="model-anthropic", base_url=base_url, timeout_seconds=30.0, transport=transport
        )
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "anthropic-version": ANTHROPIC_VERSION}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return headers

    async def generate_reply(
        self, *, system_prompt: str, messages: Sequence[ModelMessage]
    ) -> ModelReply:
        body = {
            "model": self.model_name,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
        }
        data = await self.client.request_json(
            "POST", "/messages", fallback=None, headers=self._headers(), json=body
        )
        content = _extract_content(data)
        return ModelReply(content=content if content is not None else MODEL_UNAVAILABLE_RESPONSE)


def _extract_content(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    blocks = data.get("content")
    if not isinstance(blocks, list) or not blocks:
        return None
    first = blocks[0]
    text = first.get("text") if isinstance(first, dict) else None
    return text if isinstance(text, str) and text else None
