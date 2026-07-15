from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.ha_user_mappings import resolve_mapping
from kinward.persistence.models import AssistantRecord, PersonRecord, TopicRecord, TopicTurnRecord

NO_MODEL_RESPONSE = (
    "No model provider is configured for this Kinward deployment yet, so I can't "
    "generate a real reply. This is a truthful capability report, not an error."
)


@dataclass(frozen=True)
class Unmapped:
    """The caller's HA user has no account-bearing Kinward profile mapped - fail closed."""


@dataclass(frozen=True)
class Completed:
    conversation_id: str
    response_text: str


ConversationOutcome = Unmapped | Completed


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
    person_id = await resolve_mapping(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()

    topic: TopicRecord | None = None
    if conversation_id:
        topic = await _find_own_topic(session, topic_id=conversation_id, person_id=person_id)
    if topic is None:
        assistant = await _find_primary_assistant(session, person_id)
        assert assistant is not None, "bootstrap guarantees every account-bearing person has one"
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
