"""Compatibility exports for the neutral memory subsystem.

New code should import from ``kinward.memory`` directly.
"""

from kinward.memory import (
    ConversationMessage,
    ConversationalMemoryProvider,
    KnowledgeFact,
    KnowledgeStoreProvider,
    MemoryHit,
    conversational_memory_provider,
    knowledge_store_provider,
)

__all__ = [
    "ConversationMessage",
    "ConversationalMemoryProvider",
    "KnowledgeFact",
    "KnowledgeStoreProvider",
    "MemoryHit",
    "conversational_memory_provider",
    "knowledge_store_provider",
]
