from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.conversation import (
    AlreadyTerminal,
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
from kinward.application.ha_user_mappings import upsert_mapping
from kinward.persistence.models import (
    AccountRecord,
    AssistantRecord,
    Base,
    HouseholdRecord,
    PersonRecord,
    TopicRecord,
    TopicTurnRecord,
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
        household_id=household.id, display_name="Example Adult", role="admin", profile_kind="adult"
    )
    session.add(person)
    await session.flush()
    session.add_all(
        [
            AccountRecord(
                household_id=household.id,
                person_id=person.id,
                email="adult@example.invalid",
                password_verifier="x",
            ),
            AssistantRecord(
                household_id=household.id, owner_person_id=person.id, name="Atlas", kind="primary"
            ),
        ]
    )
    await session.flush()
    await upsert_mapping(session, ha_user_id="ha-user-1", person_id=person.id)
    await session.commit()
    return household, person


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
        other_person = PersonRecord(
            household_id=household.id, display_name="Other Adult", role="member", profile_kind="adult"
        )
        session.add(other_person)
        await session.flush()
        session.add_all(
            [
                AccountRecord(
                    household_id=household.id,
                    person_id=other_person.id,
                    email="other@example.invalid",
                    password_verifier="x",
                ),
                AssistantRecord(
                    household_id=household.id,
                    owner_person_id=other_person.id,
                    name="Nova",
                    kind="primary",
                ),
            ]
        )
        await session.flush()
        await upsert_mapping(session, ha_user_id="ha-user-2", person_id=other_person.id)
        await session.commit()

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
        other_person = PersonRecord(
            household_id=household.id, display_name="Other Adult", role="member", profile_kind="adult"
        )
        session.add(other_person)
        await session.flush()
        session.add_all(
            [
                AccountRecord(
                    household_id=household.id,
                    person_id=other_person.id,
                    email="other2@example.invalid",
                    password_verifier="x",
                ),
                AssistantRecord(
                    household_id=household.id,
                    owner_person_id=other_person.id,
                    name="Nova",
                    kind="primary",
                ),
            ]
        )
        await session.flush()
        await upsert_mapping(session, ha_user_id="ha-user-2", person_id=other_person.id)
        await session.commit()

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
        other_person = PersonRecord(
            household_id=household.id, display_name="Other Adult", role="member", profile_kind="adult"
        )
        session.add(other_person)
        await session.flush()
        session.add_all(
            [
                AccountRecord(
                    household_id=household.id,
                    person_id=other_person.id,
                    email="other3@example.invalid",
                    password_verifier="x",
                ),
                AssistantRecord(
                    household_id=household.id,
                    owner_person_id=other_person.id,
                    name="Nova",
                    kind="primary",
                ),
            ]
        )
        await session.flush()
        await upsert_mapping(session, ha_user_id="ha-user-2", person_id=other_person.id)
        await session.commit()

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
