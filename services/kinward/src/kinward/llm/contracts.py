from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

ModelRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class ModelMessage:
    role: ModelRole
    content: str


@dataclass(frozen=True)
class ModelReply:
    content: str


class ModelProvider(Protocol):
    name: str

    async def generate_reply(
        self, *, system_prompt: str, messages: Sequence[ModelMessage]
    ) -> ModelReply: ...
