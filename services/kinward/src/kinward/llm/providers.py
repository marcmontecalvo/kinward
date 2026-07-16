from __future__ import annotations

from typing import Sequence

from kinward.llm.contracts import ModelMessage, ModelReply

NO_MODEL_RESPONSE = (
    "No model provider is configured for this Kinward deployment yet, so I can't "
    "generate a real reply. This is a truthful capability report, not an error."
)

MODEL_UNAVAILABLE_RESPONSE = (
    "The configured model provider could not be reached just now, so I can't "
    "generate a real reply. This is a truthful capability report, not an error."
)


class NullModelProvider:
    """Truthful degraded state: never fabricates a reply when no model is configured."""

    name = "none"

    async def generate_reply(
        self, *, system_prompt: str, messages: Sequence[ModelMessage]
    ) -> ModelReply:
        return ModelReply(content=NO_MODEL_RESPONSE)
