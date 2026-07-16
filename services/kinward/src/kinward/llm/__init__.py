"""Neutral model-provider interface for generating conversation replies."""

from kinward.llm.contracts import ModelMessage, ModelProvider, ModelReply
from kinward.llm.factory import model_provider

__all__ = [
    "ModelMessage",
    "ModelProvider",
    "ModelReply",
    "model_provider",
]
