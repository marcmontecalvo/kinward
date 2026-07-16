from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import AssistantRecord, PersonRecord, TopicRecord, TopicTurnRecord

NO_MODEL_RESPONSE = (
    "No model provider is configured for this Kinward deployment yet, so I can't "
    "generate a real reply. This is a truthful capability report, not an error."
)


@dataclass(frozen=True)
class Unmapped:
    """The caller's HA user id isn't linked to any synced Kinward person - fail closed."""


@dataclass(frozen=True)
class Completed:
    conversation_id: str
    response_text: str


ConversationOutcome = Unmapped | Completed

TERMINAL_OUTCOMES = frozenset({"completed", "failed", "cancelled"})


@dataclass(frozen=True)
class TurnNotFound:
    """No such turn, or it doesn't belong to the resolved person - fail closed either way."""


@dataclass(frozen=True)
class AlreadyTerminal:
    turn_id: str
    outcome: str


CancelOutcome = Unmapped | TurnNotFound | AlreadyTerminal


async def _resolve_person_id(session: AsyncSession, *, ha_user_id: str) -> str | None:
    """Fail-closed resolver: None for an HA user not linked to any synced person."""
    person_id: str | None = await session.scalar(
        select(PersonRecord.id).where(PersonRecord.ha_user_id == ha_user_id)
    )
    return person_id


async def _find_primary_assistant(session: AsyncSession, person_id: str) -> AssistantRecord | None:
    assistant = await session.scalar(
        select(AssistantRecord).where(
            AssistantRecord.owner_person_id == person_id, AssistantRecord.kind == "primary"
        )
    )
    return assistant


async def _find_own_topic(
    session: AsyncSession, *, topic_id: str, person_id: str
) -> TopicRecord | None:
    """Only ever continues a topic that belongs to the resolved person - never another's."""
    topic = await session.get(TopicRecord, topic_id)
    if topic is None or topic.person_id != person_id:
        return None
    return topic


async def handle_conversation_request(
    session: AsyncSession,
    *,
    ha_user_id: str,
    text: str,
    conversation_id: str | None,
    language: str,
) -> ConversationOutcome:
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()

    topic: TopicRecord | None = None
    if conversation_id:
        topic = await _find_own_topic(session, topic_id=conversation_id, person_id=person_id)
    if topic is None:
        assistant = await _find_primary_assistant(session, person_id)
        assert assistant is not None, "sync creates a primary assistant atomically with every person"
        person = await session.get(PersonRecord, person_id)
        assert person is not None
        topic = TopicRecord(
            household_id=person.household_id, person_id=person_id, assistant_id=assistant.id
        )
        session.add(topic)
        await session.flush()

    session.add(
        TopicTurnRecord(
            topic_id=topic.id,
            request_text=text,
            response_text=NO_MODEL_RESPONSE,
            outcome="completed",
        )
    )
    await session.flush()
    return Completed(conversation_id=topic.id, response_text=NO_MODEL_RESPONSE)


async def cancel_turn(session: AsyncSession, *, turn_id: str, ha_user_id: str) -> CancelOutcome:
    """Report cancellation state for a turn.

    Every turn is created with a terminal outcome in the same call that creates it - there is
    no async/model work yet that could ever leave one mid-flight - so this always reports
    ``AlreadyTerminal`` today. It is the real interface future async/streaming work will give
    teeth to (an in-flight turn found here would actually transition to "cancelled"), not
    fabricated behavior: "exactly one terminal outcome is recorded" already holds because turns
    are append-only and never mutated after creation.
    """
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()

    turn = await session.get(TopicTurnRecord, turn_id)
    if turn is None:
        return TurnNotFound()
    topic = await session.get(TopicRecord, turn.topic_id)
    if topic is None or topic.person_id != person_id:
        return TurnNotFound()

    assert turn.outcome in TERMINAL_OUTCOMES, "turns are always created with a terminal outcome today"
    return AlreadyTerminal(turn_id=turn.id, outcome=turn.outcome)


@dataclass(frozen=True)
class TopicNotFound:
    """No such topic, or it doesn't belong to the resolved person - fail closed either way."""


@dataclass(frozen=True)
class Deleted:
    topic_id: str


TopicState = Literal["open", "archived"]


async def list_topics(session: AsyncSession, *, ha_user_id: str) -> list[TopicRecord] | Unmapped:
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()
    topics = await session.scalars(
        select(TopicRecord)
        .where(TopicRecord.person_id == person_id)
        .order_by(TopicRecord.updated_at.desc())
    )
    return list(topics)


async def get_topic(
    session: AsyncSession, *, ha_user_id: str, topic_id: str
) -> TopicRecord | TopicNotFound | Unmapped:
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()
    topic = await _find_own_topic(session, topic_id=topic_id, person_id=person_id)
    if topic is None:
        return TopicNotFound()
    return topic


async def update_topic(
    session: AsyncSession,
    *,
    ha_user_id: str,
    topic_id: str,
    title: str | None = None,
    state: TopicState | None = None,
) -> TopicRecord | TopicNotFound | Unmapped:
    """Partial update: only fields explicitly passed are changed (rename and/or archive/reopen)."""
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()
    topic = await _find_own_topic(session, topic_id=topic_id, person_id=person_id)
    if topic is None:
        return TopicNotFound()
    if title is not None:
        topic.title = title
    if state is not None:
        topic.state = state
    topic.record_version += 1
    await session.flush()
    return topic


async def delete_topic(
    session: AsyncSession, *, ha_user_id: str, topic_id: str
) -> Deleted | TopicNotFound | Unmapped:
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()
    topic = await _find_own_topic(session, topic_id=topic_id, person_id=person_id)
    if topic is None:
        return TopicNotFound()
    await session.delete(topic)
    await session.flush()
    return Deleted(topic_id=topic_id)
