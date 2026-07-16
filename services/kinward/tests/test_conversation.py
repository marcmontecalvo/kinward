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
from kinward.memory.honcho import HonchoMemoryProvider
from kinward.persistence.models import (
    AssistantRecord,
    Base,
    HouseholdRecord,
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
