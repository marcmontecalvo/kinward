from __future__ import annotations

import httpx

from kinward.config import Settings
from kinward.memory.contracts import ConversationMessage
from kinward.memory.factory import conversational_memory_provider, knowledge_store_provider
from kinward.memory.honcho import HonchoMemoryProvider
from kinward.memory.llm_wiki import LlmWikiKnowledgeProvider


async def test_provider_factory_supports_none() -> None:
    settings = Settings(memory_backend="none", knowledge_backend="none")
    assert conversational_memory_provider(settings).name == "none"
    assert knowledge_store_provider(settings).name == "none"


async def test_honcho_provider_appends_and_recalls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/messages"):
            return httpx.Response(201, json={"items": [{"id": "m1"}]})
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": [{"id": "m1", "content": "Likes tea", "score": 0.9}]})
        return httpx.Response(201, json={})

    provider = HonchoMemoryProvider(
        base_url="http://honcho.invalid",
        transport=httpx.MockTransport(handler),
    )
    ids = await provider.append_messages(
        household_id="house",
        person_id="person",
        assistant_id="assistant",
        messages=[ConversationMessage(role="user", content="I like tea")],
    )
    assert ids == ["m1"]

    hits = await provider.recall(
        household_id="house",
        person_id="person",
        assistant_id="assistant",
        query="tea",
    )
    assert hits[0].content == "Likes tea"


async def test_llm_wiki_provider_proposes_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = {
            "key": "person.favorite_drink",
            "value": {
                "subject": "person",
                "predicate": "favorite_drink",
                "value": "tea",
            },
            "status": "proposed",
            "visibility": "personal",
            "confidence": 0.8,
            "provenance": [{"reference": "conversation:m1"}],
        }
        return httpx.Response(200, json=payload)

    provider = LlmWikiKnowledgeProvider(
        base_url="http://wiki.invalid",
        transport=httpx.MockTransport(handler),
    )
    fact = await provider.propose_fact(
        household_id="house",
        person_id="person",
        assistant_id="assistant",
        subject="person",
        predicate="favorite_drink",
        value="tea",
        privacy="personal",
        provenance=["conversation:m1"],
        confidence=0.8,
    )
    assert fact.value == "tea"
    assert fact.status == "proposed"
