from __future__ import annotations

import json

import httpx

from kinward.memory.contracts import ConversationMessage
from kinward.memory.factory import conversational_memory_provider, knowledge_store_provider
from kinward.memory.honcho import HonchoMemoryProvider
from kinward.memory.llm_wiki import LlmWikiKnowledgeProvider


async def test_provider_factory_supports_none() -> None:
    assert conversational_memory_provider(backend="none", url=None).name == "none"
    assert knowledge_store_provider(backend="none", url=None).name == "none"


async def test_provider_factory_requires_a_url_even_when_a_backend_is_named() -> None:
    assert conversational_memory_provider(backend="honcho", url=None).name == "none"
    assert knowledge_store_provider(backend="llm_wiki", url=None).name == "none"


async def test_honcho_provider_appends_and_recalls() -> None:
    """Honcho's real message-create and search routes return a bare ``list[Message]``,

    not ``{"items": [...]}`` (confirmed against a real Honcho instance) - the mocked
    responses here match that actual wire shape, not a guess.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/messages"):
            return httpx.Response(201, json=[{"id": "m1"}])
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json=[{"id": "m1", "content": "Likes tea", "score": 0.9}])
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


async def test_honcho_provider_also_accepts_a_paginated_items_wrapper() -> None:
    """Defensive: the export path's ``/messages/list`` route is genuinely paginated

    (``Page[Message]``, wrapped in ``{"items": [...]}``); recall/append tolerate the
    same shape too in case a future Honcho version wraps them the same way.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": [{"id": "m1", "content": "Likes tea"}]})
        return httpx.Response(201, json={})

    provider = HonchoMemoryProvider(
        base_url="http://honcho.invalid",
        transport=httpx.MockTransport(handler),
    )
    hits = await provider.recall(
        household_id="house", person_id="person", assistant_id="assistant", query="tea"
    )
    assert hits[0].content == "Likes tea"


async def test_honcho_session_creation_sends_peers_as_a_mapping_not_a_list() -> None:
    """Honcho's SessionCreate schema requires `peers: dict[str, SessionPeerConfig]` -

    a list 422s on every call. Session auto-creation on first message masked this in
    production (nothing user-visible broke), but the explicit session-creation request
    itself silently failed every time.
    """
    seen_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/sessions"):
            seen_bodies.append(json.loads(request.content))
        return httpx.Response(201, json={})

    provider = HonchoMemoryProvider(
        base_url="http://honcho.invalid",
        transport=httpx.MockTransport(handler),
    )
    await provider.append_messages(
        household_id="house",
        person_id="person",
        assistant_id="assistant",
        messages=[ConversationMessage(role="user", content="hi")],
    )

    assert len(seen_bodies) == 1
    peers = seen_bodies[0]["peers"]
    assert isinstance(peers, dict)
    assert set(peers) == {"person_person", "assistant_assistant"}


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


async def test_llm_wiki_provider_reclassifies_fact_visibility() -> None:
    seen_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "key": "person.favorite_drink",
                    "value": {"subject": "person", "predicate": "favorite_drink", "value": "tea"},
                    "status": "confirmed",
                    "visibility": "personal",
                    "confidence": 0.8,
                    "provenance": [],
                },
            )
        body = json.loads(request.content)
        seen_bodies.append(body)
        return httpx.Response(200, json=body)

    provider = LlmWikiKnowledgeProvider(
        base_url="http://wiki.invalid",
        transport=httpx.MockTransport(handler),
    )
    fact = await provider.reclassify_fact(
        fact_id="kinward_house::person.favorite_drink", privacy="household"
    )
    assert fact is not None
    assert fact.privacy == "household"
    assert seen_bodies[0]["visibility"] == "household"
