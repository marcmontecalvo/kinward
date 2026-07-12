"""Neutral conversational-memory and curated-knowledge provider interfaces."""

from kinward.memory.contracts import (
    ConversationMessage,
    ConversationalMemoryProvider,
    KnowledgeFact,
    KnowledgeStoreProvider,
    MemoryHit,
)
from kinward.memory.factory import conversational_memory_provider, knowledge_store_provider

__all__ = [
    "ConversationMessage",
    "ConversationalMemoryProvider",
    "KnowledgeFact",
    "KnowledgeStoreProvider",
    "MemoryHit",
    "conversational_memory_provider",
    "knowledge_store_provider",
]
