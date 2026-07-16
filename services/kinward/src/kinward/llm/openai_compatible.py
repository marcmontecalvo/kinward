from __future__ import annotations

from typing import Any, Sequence

from kinward.integrations.base import IntegrationClient
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.llm.providers import MODEL_UNAVAILABLE_RESPONSE


class OpenAiCompatibleModelProvider:
    """Adapter for OpenAI's own API and any OpenAI-chat-completions-compatible
    self-hosted server (Ollama, vLLM, llama.cpp server, LM Studio, ...).

    ``base_url`` is the API root including any version prefix the server
    expects (e.g. ``https://api.openai.com/v1`` or ``http://ollama.local:11434/v1``)
    - ``/chat/completions`` is appended to it.
    """

    name = "openai"

    def __init__(self, *, base_url: str, model_name: str, api_key: str | None, transport: Any = None) -> None:
        self.model_name = model_name
        self.client = IntegrationClient(
            name="model-openai-compatible", base_url=base_url, timeout_seconds=30.0, transport=transport
        )
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def generate_reply(
        self, *, system_prompt: str, messages: Sequence[ModelMessage]
    ) -> ModelReply:
        body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                *({"role": message.role, "content": message.content} for message in messages),
            ],
        }
        data = await self.client.request_json(
            "POST", "/chat/completions", fallback=None, headers=self._headers(), json=body
        )
        content = _extract_content(data)
        return ModelReply(content=content if content is not None else MODEL_UNAVAILABLE_RESPONSE)


def _extract_content(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    return content if isinstance(content, str) and content else None
