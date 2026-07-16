from __future__ import annotations

from kinward.memory.contracts import ConversationalMemoryProvider, KnowledgeStoreProvider
from kinward.memory.honcho import HonchoMemoryProvider
from kinward.memory.llm_wiki import LlmWikiKnowledgeProvider
from kinward.memory.providers import NullConversationalMemoryProvider, NullKnowledgeStoreProvider


def conversational_memory_provider(
    *, backend: str, url: str | None
) -> ConversationalMemoryProvider:
    if backend == "honcho" and url:
        return HonchoMemoryProvider(base_url=url)
    return NullConversationalMemoryProvider()


def knowledge_store_provider(*, backend: str, url: str | None) -> KnowledgeStoreProvider:
    if backend == "llm_wiki" and url:
        return LlmWikiKnowledgeProvider(base_url=url)
    return NullKnowledgeStoreProvider()
