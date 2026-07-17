from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.conversation import (
    AccessDenied,
    AlreadyTerminal,
    AssistantNotFound,
    Completed,
    Deleted,
    TopicNotFound,
    TurnNotFound,
    Unmapped,
    cancel_turn,
    delete_topic,
    get_topic,
    handle_conversation_request,
    list_topics,
    update_topic,
)
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.llm.providers import NO_MODEL_RESPONSE
from kinward.memory.contracts import KnowledgeFact
from kinward.memory.honcho import HonchoMemoryProvider
from kinward.persistence.models import (
    AssistantRecord,
    Base,
    HouseholdRecord,
    KnowledgeFactRecord,
    PersonRecord,
    TopicRecord,
    TopicTurnRecord,
)


@dataclass
class RecordingModelProvider:
    """Fake model that echoes a canned reply and records every call it received."""

    name: str = "fake"
    reply_text: str = "This is a real generated reply."
    calls: list[tuple[str, tuple[ModelMessage, ...]]] = field(default_factory=list)

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        self.calls.append((system_prompt, tuple(messages)))
        return ModelReply(content=self.reply_text)


@dataclass
class TwoStageModelProvider:
    """Fake model returning ``reply_text`` for the first call (the turn's reply) and

    ``extraction_json`` for every call after that (the Story 4.3 structured-extraction step).
    """

    name: str = "fake"
    reply_text: str = "Got it, I'll remember that."
    extraction_json: str = '{"observations": []}'
    calls: list[tuple[str, tuple[ModelMessage, ...]]] = field(default_factory=list)

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        self.calls.append((system_prompt, tuple(messages)))
        content = self.reply_text if len(self.calls) == 1 else self.extraction_json
        return ModelReply(content=content)


@dataclass
class RecordingKnowledgeProvider:
    """Fake ``KnowledgeStoreProvider`` that records every ``propose_fact`` call it receives."""

    name: str = "fake-knowledge"
    calls: list[dict] = field(default_factory=list)
    _counter: int = 0

    async def search_facts(self, **kwargs) -> list:  # type: ignore[no-untyped-def]
        return []

    async def propose_fact(self, **kwargs) -> KnowledgeFact:  # type: ignore[no-untyped-def]
        self._counter += 1
        self.calls.append(kwargs)
        return KnowledgeFact(
            id=f"fake-fact-{self._counter}",
            subject=kwargs["subject"],
            predicate=kwargs["predicate"],
            value=kwargs["value"],
            status="proposed",
            privacy=kwargs["privacy"],
        )


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_mapped_person(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Example Adult",
        role="admin",
        profile_kind="adult",
        ha_person_id="ha-person-1",
        ha_user_id="ha-user-1",
    )
    session.add(person)
    await session.flush()
    session.add(
        AssistantRecord(
            household_id=household.id, owner_person_id=person.id, name="Atlas", kind="primary"
        )
    )
    await session.commit()
    return household, person


async def _add_other_mapped_person(session, household, *, ha_person_id: str, ha_user_id: str, assistant_name: str = "Nova"):  # type: ignore[no-untyped-def]
    other_person = PersonRecord(
        household_id=household.id,
        display_name="Other Adult",
        role="member",
        profile_kind="adult",
        ha_person_id=ha_person_id,
        ha_user_id=ha_user_id,
    )
    session.add(other_person)
    await session.flush()
    session.add(
        AssistantRecord(
            household_id=household.id,
            owner_person_id=other_person.id,
            name=assistant_name,
            kind="primary",
        )
    )
    await session.commit()
    return other_person


async def test_unmapped_ha_user_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        result = await handle_conversation_request(
            session, ha_user_id="unknown-ha-user", text="hello", conversation_id=None, language="en"
        )
        assert isinstance(result, Unmapped)


async def test_mapped_request_creates_a_topic_and_turn() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person = await _seed_mapped_person(session)

        result = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()

        assert isinstance(result, Completed)
        topic = await session.get(TopicRecord, result.conversation_id)
        assert topic is not None
        assert topic.person_id == person.id
        turns = (
            await session.scalars(select(TopicTurnRecord).where(TopicTurnRecord.topic_id == topic.id))
        ).all()
        assert len(turns) == 1
        assert turns[0].request_text == "hello"
        assert turns[0].outcome == "completed"


async def test_same_conversation_id_continues_the_same_topic() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)

        first = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="first", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(first, Completed)

        second = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="second",
            conversation_id=first.conversation_id,
            language="en",
        )
        await session.commit()
        assert isinstance(second, Completed)
        assert second.conversation_id == first.conversation_id

        turns = (
            await session.scalars(
                select(TopicTurnRecord).where(TopicTurnRecord.topic_id == first.conversation_id)
            )
        ).all()
        assert len(turns) == 2


async def test_a_conversation_id_belonging_to_a_different_person_is_not_continued() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person_one = await _seed_mapped_person(session)
        await _add_other_mapped_person(session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2")

        owned = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="mine", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(owned, Completed)

        stolen_attempt = await handle_conversation_request(
            session,
            ha_user_id="ha-user-2",
            text="not yours",
            conversation_id=owned.conversation_id,
            language="en",
        )
        await session.commit()

        assert isinstance(stolen_attempt, Completed)
        assert stolen_attempt.conversation_id != owned.conversation_id


async def test_cancel_unmapped_ha_user_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        result = await cancel_turn(session, turn_id="does-not-exist", ha_user_id="unknown-ha-user")
        assert isinstance(result, Unmapped)


async def test_cancel_unknown_turn_reports_not_found() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        result = await cancel_turn(session, turn_id="does-not-exist", ha_user_id="ha-user-1")
        assert isinstance(result, TurnNotFound)


async def test_cancel_reports_a_real_turn_as_already_terminal() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        completed = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(completed, Completed)

        turn = (
            await session.scalars(
                select(TopicTurnRecord).where(TopicTurnRecord.topic_id == completed.conversation_id)
            )
        ).one()

        result = await cancel_turn(session, turn_id=turn.id, ha_user_id="ha-user-1")
        assert isinstance(result, AlreadyTerminal)
        assert result.turn_id == turn.id
        assert result.outcome == "completed"

        # cancelling never mutates the already-terminal turn
        unchanged = await session.get(TopicTurnRecord, turn.id)
        assert unchanged is not None
        assert unchanged.outcome == "completed"


async def test_cancel_does_not_let_a_different_person_cancel_another_persons_turn() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person_one = await _seed_mapped_person(session)
        await _add_other_mapped_person(session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2")

        owned = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="mine", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(owned, Completed)
        turn = (
            await session.scalars(
                select(TopicTurnRecord).where(TopicTurnRecord.topic_id == owned.conversation_id)
            )
        ).one()

        result = await cancel_turn(session, turn_id=turn.id, ha_user_id="ha-user-2")
        assert isinstance(result, TurnNotFound)


async def test_list_topics_only_shows_the_resolved_persons_topics() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)

        assert await list_topics(session, ha_user_id="unknown-ha-user") == Unmapped()
        assert await list_topics(session, ha_user_id="ha-user-1") == []

        completed = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(completed, Completed)

        topics = await list_topics(session, ha_user_id="ha-user-1")
        assert isinstance(topics, list)
        assert [topic.id for topic in topics] == [completed.conversation_id]


async def test_get_topic_fails_closed_for_unmapped_and_unknown() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        assert isinstance(
            await get_topic(session, ha_user_id="unknown-ha-user", topic_id="whatever"), Unmapped
        )
        assert isinstance(
            await get_topic(session, ha_user_id="ha-user-1", topic_id="does-not-exist"),
            TopicNotFound,
        )


async def test_rename_and_archive_and_reopen_a_topic() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        completed = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(completed, Completed)
        topic_id = completed.conversation_id

        renamed = await update_topic(
            session, ha_user_id="ha-user-1", topic_id=topic_id, title="Weekend plans"
        )
        await session.commit()
        assert not isinstance(renamed, (Unmapped, TopicNotFound))
        assert renamed.title == "Weekend plans"
        assert renamed.state == "open"

        archived = await update_topic(
            session, ha_user_id="ha-user-1", topic_id=topic_id, state="archived"
        )
        await session.commit()
        assert not isinstance(archived, (Unmapped, TopicNotFound))
        assert archived.state == "archived"
        assert archived.title == "Weekend plans"

        reopened = await update_topic(session, ha_user_id="ha-user-1", topic_id=topic_id, state="open")
        await session.commit()
        assert not isinstance(reopened, (Unmapped, TopicNotFound))
        assert reopened.state == "open"


async def test_update_topic_fails_closed_for_another_persons_topic() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person_one = await _seed_mapped_person(session)
        await _add_other_mapped_person(session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2")

        owned = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="mine", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(owned, Completed)

        result = await update_topic(
            session, ha_user_id="ha-user-2", topic_id=owned.conversation_id, title="not yours"
        )
        assert isinstance(result, TopicNotFound)


async def test_delete_topic_removes_it_and_its_turns() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        completed = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(completed, Completed)
        topic_id = completed.conversation_id

        result = await delete_topic(session, ha_user_id="ha-user-1", topic_id=topic_id)
        await session.commit()
        assert result == Deleted(topic_id=topic_id)

        assert await session.get(TopicRecord, topic_id) is None
        remaining_turns = (
            await session.scalars(select(TopicTurnRecord).where(TopicTurnRecord.topic_id == topic_id))
        ).all()
        assert remaining_turns == []


async def test_default_none_model_still_reports_the_truthful_capability_message() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        result = await handle_conversation_request(
            session, ha_user_id="ha-user-1", text="hello", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(result, Completed)
        assert result.response_text == NO_MODEL_RESPONSE


async def test_a_configured_model_generates_a_real_reply_and_sees_prior_turns_as_history() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()

        first = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            model=model,
        )
        await session.commit()
        assert isinstance(first, Completed)
        assert first.response_text == model.reply_text

        second = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="second message",
            conversation_id=first.conversation_id,
            language="en",
            model=model,
        )
        await session.commit()
        assert isinstance(second, Completed)

        assert len(model.calls) == 2
        _first_prompt, first_messages = model.calls[0]
        assert first_messages[-1] == ModelMessage(role="user", content="hello")

        _second_prompt, second_messages = model.calls[1]
        assert second_messages[0] == ModelMessage(role="user", content="hello")
        assert second_messages[1] == ModelMessage(role="assistant", content=model.reply_text)
        assert second_messages[-1] == ModelMessage(role="user", content="second message")


async def test_home_assistant_state_is_folded_into_the_system_prompt_when_enabled() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"entity_id": "light.kitchen", "state": "on"}])

    ha_client = HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()
        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="is the kitchen light on?",
            conversation_id=None,
            language="en",
            model=model,
            ha_client=ha_client,
        )
        await session.commit()
        assert isinstance(result, Completed)
        system_prompt, _messages = model.calls[0]
        assert "light.kitchen: on" in system_prompt


async def test_home_assistant_state_is_absent_from_the_prompt_when_not_configured() -> None:
    ha_client = HomeAssistantClient(base_url=None, token=None)

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()
        await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            model=model,
            ha_client=ha_client,
        )
        await session.commit()
        system_prompt, _messages = model.calls[0]
        assert "home state" not in system_prompt.lower()


async def test_recent_device_and_timer_are_folded_into_the_system_prompt_when_resolved() -> None:
    now = datetime.now(timezone.utc)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/states":
            return httpx.Response(
                200,
                json=[
                    {
                        "entity_id": "light.office",
                        "state": "on",
                        "last_changed": (now - timedelta(minutes=1)).isoformat(),
                    },
                    {
                        "entity_id": "timer.kitchen",
                        "state": "active",
                        "last_changed": (now - timedelta(minutes=20)).isoformat(),
                    },
                ],
            )
        return httpx.Response(200, text="none")

    ha_client = HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()
        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="is the light still on?",
            conversation_id=None,
            language="en",
            device_id="device-1",
            model=model,
            ha_client=ha_client,
        )
        await session.commit()
        assert isinstance(result, Completed)
        system_prompt, _messages = model.calls[0]
        assert "light.office is on" in system_prompt
        assert "Currently active timer: timer.kitchen." in system_prompt


async def test_recent_reference_note_is_absent_when_nothing_resolves() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/states":
            return httpx.Response(200, json=[])
        return httpx.Response(200, text="none")

    ha_client = HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()
        await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            model=model,
            ha_client=ha_client,
        )
        await session.commit()
        system_prompt, _messages = model.calls[0]
        assert "recently changed" not in system_prompt.lower()
        assert "active timer" not in system_prompt.lower()


async def test_memory_recall_grounds_the_system_prompt_and_a_configured_model_appends_the_turn() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(
                200, json={"items": [{"id": "m1", "content": "Likes tea", "score": 0.9}]}
            )
        if request.url.path.endswith("/messages"):
            return httpx.Response(201, json={"items": [{"id": "m2"}]})
        return httpx.Response(201, json={})

    memory = HonchoMemoryProvider(base_url="http://honcho.invalid", transport=httpx.MockTransport(handler))

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = RecordingModelProvider()
        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="what do I like to drink?",
            conversation_id=None,
            language="en",
            model=model,
            memory_provider=memory,
        )
        await session.commit()

        assert isinstance(result, Completed)
        system_prompt, _messages = model.calls[0]
        assert "Likes tea" in system_prompt
        assert any(path.endswith("/messages") for path in seen_paths), "the new turn should be appended to memory"


async def test_memory_is_not_appended_when_no_model_is_configured() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": []})
        return httpx.Response(201, json={})

    memory = HonchoMemoryProvider(base_url="http://honcho.invalid", transport=httpx.MockTransport(handler))

    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            memory_provider=memory,
        )
        await session.commit()
        assert isinstance(result, Completed)
        assert result.response_text == NO_MODEL_RESPONSE
        assert not any(path.endswith("/messages") for path in calls)


async def _get_assistant(session, *, owner_person_id: str):  # type: ignore[no-untyped-def]
    return (
        await session.scalars(
            select(AssistantRecord).where(AssistantRecord.owner_person_id == owner_person_id)
        )
    ).one()


async def test_addressing_someone_elses_owner_only_assistant_is_denied() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person_one = await _seed_mapped_person(session)
        other = await _add_other_mapped_person(
            session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2"
        )
        nova = await _get_assistant(session, owner_person_id=other.id)
        assert nova.access_mode == "owner_only"

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello Nova",
            conversation_id=None,
            language="en",
            assistant_id=nova.id,
        )

        assert result == AccessDenied(assistant_name="Nova")


async def test_addressing_an_unknown_assistant_id_is_not_found() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            assistant_id="does-not-exist",
        )

        assert isinstance(result, AssistantNotFound)


async def test_owner_can_always_explicitly_address_their_own_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, person = await _seed_mapped_person(session)
        atlas = await _get_assistant(session, owner_person_id=person.id)

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            assistant_id=atlas.id,
        )

        assert isinstance(result, Completed)


async def test_household_mode_allows_addressing_another_persons_assistant_with_an_isolated_session() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person_one = await _seed_mapped_person(session)
        other = await _add_other_mapped_person(
            session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2"
        )
        nova = await _get_assistant(session, owner_person_id=other.id)
        nova.access_mode = "household"
        await session.commit()

        # The owner (ha-user-2) talks to their own Nova first.
        owner_result = await handle_conversation_request(
            session, ha_user_id="ha-user-2", text="hi Nova, it's me", conversation_id=None, language="en"
        )
        await session.commit()
        assert isinstance(owner_result, Completed)

        # A different household member addresses Nova explicitly - allowed under household mode.
        guest_result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hi Nova, can you check something for me",
            conversation_id=None,
            language="en",
            assistant_id=nova.id,
        )
        await session.commit()
        assert isinstance(guest_result, Completed)

        # Isolated: this is a different topic from the owner's own conversation with Nova.
        assert guest_result.conversation_id != owner_result.conversation_id
        guest_topic = await session.get(TopicRecord, guest_result.conversation_id)
        owner_topic = await session.get(TopicRecord, owner_result.conversation_id)
        assert guest_topic is not None and owner_topic is not None
        assert guest_topic.person_id == person_one.id
        assert owner_topic.person_id == other.id
        assert guest_topic.assistant_id == owner_topic.assistant_id == nova.id


async def _seed_household_fallback_assistant(session, household):  # type: ignore[no-untyped-def]
    fallback = AssistantRecord(
        household_id=household.id,
        owner_person_id=None,
        name="Kinward",
        kind="household-fallback",
        classification="household-shared",
        access_mode="household",
    )
    session.add(fallback)
    await session.commit()
    return fallback


async def test_household_fallback_assistant_never_leaks_a_persons_private_memory_into_its_context() -> None:
    """Story 2.5: a shared-display/resolved caller addressing the ownerless household
    fallback assistant must get only household-safe context - never another (or their
    own) private-assistant memory. Isolation is structural, keyed by (person, assistant)
    session id, so this seeds real private-sounding content and proves it never crosses
    into the fallback assistant's session for either the owner or a different person.
    """
    factory = await _factory()
    async with factory() as session:
        household, person_one = await _seed_mapped_person(session)
        person_two = await _add_other_mapped_person(
            session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2"
        )
        atlas = await _get_assistant(session, owner_person_id=person_one.id)
        fallback = await _seed_household_fallback_assistant(session, household)

        private_session_id = HonchoMemoryProvider.session_id(person_one.id, atlas.id)
        fallback_session_for_person_one = HonchoMemoryProvider.session_id(person_one.id, fallback.id)
        fallback_session_for_person_two = HonchoMemoryProvider.session_id(person_two.id, fallback.id)

        seen_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_paths.append(request.url.path)
            if request.url.path.endswith("/search"):
                if private_session_id in request.url.path:
                    return httpx.Response(
                        200,
                        json={"items": [{"id": "m1", "content": "Allergic to peanuts", "score": 0.9}]},
                    )
                return httpx.Response(200, json={"items": []})
            return httpx.Response(201, json={"items": [{"id": "m2"}]})

        memory = HonchoMemoryProvider(base_url="http://honcho.invalid", transport=httpx.MockTransport(handler))

        # Sanity check: the person's own conversation with their own assistant does see
        # their private memory - proves the mock actually grounds the prompt when asked.
        own_model = RecordingModelProvider()
        own_result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="what should I avoid eating?",
            conversation_id=None,
            language="en",
            model=own_model,
            memory_provider=memory,
        )
        await session.commit()
        assert isinstance(own_result, Completed)
        assert private_session_id in seen_paths[-1]
        own_prompt, _own_messages = own_model.calls[0]
        assert "Allergic to peanuts" in own_prompt

        # The same person, explicitly addressing the shared household-fallback
        # assistant, is a different (person, assistant) session and must not see
        # their own private memory folded into the prompt.
        seen_paths.clear()
        fallback_model_owner = RecordingModelProvider()
        fallback_result_owner = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="what should I avoid eating?",
            conversation_id=None,
            language="en",
            assistant_id=fallback.id,
            model=fallback_model_owner,
            memory_provider=memory,
        )
        await session.commit()
        assert isinstance(fallback_result_owner, Completed)
        assert any(fallback_session_for_person_one in path for path in seen_paths)
        assert not any(private_session_id in path for path in seen_paths)
        fallback_prompt_owner, _fallback_messages_owner = fallback_model_owner.calls[0]
        assert "Allergic to peanuts" not in fallback_prompt_owner

        # A different resolved person - standing in for a shared-display/kiosk request
        # with no assistant of its own - addressing the same fallback assistant also
        # gets only its own (empty) household-safe context, never person one's memory.
        seen_paths.clear()
        fallback_model_other = RecordingModelProvider()
        fallback_result_other = await handle_conversation_request(
            session,
            ha_user_id="ha-user-2",
            text="what should I avoid eating?",
            conversation_id=None,
            language="en",
            assistant_id=fallback.id,
            model=fallback_model_other,
            memory_provider=memory,
        )
        await session.commit()
        assert isinstance(fallback_result_other, Completed)
        assert any(fallback_session_for_person_two in path for path in seen_paths)
        assert not any(private_session_id in path for path in seen_paths)
        fallback_prompt_other, _fallback_messages_other = fallback_model_other.calls[0]
        assert "Allergic to peanuts" not in fallback_prompt_other

        # The two fallback conversations are themselves isolated topics.
        assert fallback_result_owner.conversation_id != fallback_result_other.conversation_id


async def test_allowlist_mode_allows_only_listed_people() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person_one = await _seed_mapped_person(session)
        other = await _add_other_mapped_person(
            session, household, ha_person_id="ha-person-2", ha_user_id="ha-user-2"
        )
        third = await _add_other_mapped_person(
            session, household, ha_person_id="ha-person-3", ha_user_id="ha-user-3", assistant_name="Rex"
        )
        nova = await _get_assistant(session, owner_person_id=other.id)
        nova.access_mode = "allowlist"
        nova.allowed_person_ids = [person_one.id]
        await session.commit()

        allowed = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hi Nova",
            conversation_id=None,
            language="en",
            assistant_id=nova.id,
        )
        assert isinstance(allowed, Completed)

        denied = await handle_conversation_request(
            session,
            ha_user_id="ha-user-3",
            text="hi Nova",
            conversation_id=None,
            language="en",
            assistant_id=nova.id,
        )
        assert denied == AccessDenied(assistant_name="Nova")
        _ = third


async def test_a_configured_model_and_knowledge_provider_proposes_an_extracted_observation() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _person = await _seed_mapped_person(session)
        model = TwoStageModelProvider(
            extraction_json=(
                '{"observations": [{"subject": "Example Adult", "predicate": "likes", '
                '"value": "tea", "privacy": "personal", "confidence": 0.9}]}'
            )
        )
        knowledge = RecordingKnowledgeProvider()

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="I really like tea in the mornings.",
            conversation_id=None,
            language="en",
            model=model,
            knowledge_provider=knowledge,
        )
        await session.commit()

        assert isinstance(result, Completed)
        assert len(model.calls) == 2
        assert len(knowledge.calls) == 1
        assert knowledge.calls[0]["subject"] == "Example Adult"
        assert knowledge.calls[0]["predicate"] == "likes"
        assert knowledge.calls[0]["value"] == "tea"

        records = (
            await session.scalars(
                select(KnowledgeFactRecord).where(KnowledgeFactRecord.household_id == household.id)
            )
        ).all()
        assert len(records) == 1
        assert records[0].knowledge_state == "pending"
        assert records[0].source_system == "conversation-inference"


async def test_extraction_is_skipped_without_a_configured_knowledge_provider() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = TwoStageModelProvider(
            extraction_json='{"observations": [{"subject": "x", "predicate": "y", "value": "z", "privacy": "personal"}]}'
        )

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="I really like tea.",
            conversation_id=None,
            language="en",
            model=model,
        )
        await session.commit()

        assert isinstance(result, Completed)
        assert len(model.calls) == 1


async def test_an_extraction_reply_with_no_observations_proposes_nothing() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_mapped_person(session)
        model = TwoStageModelProvider(extraction_json='{"observations": []}')
        knowledge = RecordingKnowledgeProvider()

        result = await handle_conversation_request(
            session,
            ha_user_id="ha-user-1",
            text="hello",
            conversation_id=None,
            language="en",
            model=model,
            knowledge_provider=knowledge,
        )
        await session.commit()

        assert isinstance(result, Completed)
        assert len(model.calls) == 2
        assert knowledge.calls == []
