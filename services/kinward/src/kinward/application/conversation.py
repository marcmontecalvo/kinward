from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.provider_settings import get_or_create_provider_settings
from kinward.config import Settings, get_settings
from kinward.domain.assistant_access import can_address_assistant
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.llm.contracts import ModelMessage, ModelProvider
from kinward.llm.factory import model_provider as build_model_provider
from kinward.memory.contracts import (
    ConversationMessage,
    ConversationalMemoryProvider,
    KnowledgeStoreProvider,
)
from kinward.memory.factory import conversational_memory_provider, knowledge_store_provider
from kinward.persistence.models import AssistantRecord, PersonRecord, TopicRecord, TopicTurnRecord

MAX_HOME_STATE_ENTITIES = 300
MEMORY_RECALL_LIMIT = 5
KNOWLEDGE_SEARCH_LIMIT = 5


@dataclass(frozen=True)
class Unmapped:
    """The caller's HA user id isn't linked to any synced Kinward person - fail closed."""


@dataclass(frozen=True)
class Completed:
    conversation_id: str
    response_text: str


@dataclass(frozen=True)
class AssistantNotFound:
    """The explicitly addressed assistant_id doesn't exist in this household - fail closed."""


@dataclass(frozen=True)
class AccessDenied:
    """The caller may not address this assistant under its configured ADR-002 access mode."""

    assistant_name: str


ConversationOutcome = Unmapped | Completed | AssistantNotFound | AccessDenied

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
    """The caller's own assistant when none is explicitly addressed (ADR-002).

    A person may now own several (epics.md Story 3.4) - deterministically picks the
    oldest rather than an arbitrary one. Which of several a given request addresses
    (wake-word/name routing) remains out of scope; this is only the default.
    """
    assistant = await session.scalar(
        select(AssistantRecord)
        .where(AssistantRecord.owner_person_id == person_id, AssistantRecord.kind == "primary")
        .order_by(AssistantRecord.created_at)
        .limit(1)
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


async def _prior_turns(session: AsyncSession, *, topic_id: str) -> list[TopicTurnRecord]:
    turns = await session.scalars(
        select(TopicTurnRecord)
        .where(TopicTurnRecord.topic_id == topic_id)
        .order_by(TopicTurnRecord.created_at)
    )
    return list(turns)


def _home_state_summary(states: list[dict[str, object]]) -> str | None:
    lines: list[str] = []
    for entity in states:
        entity_id = entity.get("entity_id")
        state = entity.get("state")
        if not isinstance(entity_id, str) or not isinstance(state, str):
            continue
        lines.append(f"{entity_id}: {state}")
    if not lines:
        return None
    lines.sort()
    return "\n".join(lines[:MAX_HOME_STATE_ENTITIES])


def _build_system_prompt(
    *,
    assistant: AssistantRecord,
    person: PersonRecord,
    home_state: str | None,
    memory_lines: list[str],
    knowledge_lines: list[str],
) -> str:
    sections = [
        f"You are {assistant.name}, {person.display_name}'s private Kinward household assistant."
    ]
    if assistant.personality:
        sections.append(f"Personality preferences: {assistant.personality}")
    if home_state:
        sections.append("Current home state (entity: state):\n" + home_state)
    if memory_lines:
        sections.append("Relevant things you remember about this person:\n" + "\n".join(memory_lines))
    if knowledge_lines:
        sections.append("Known household facts:\n" + "\n".join(knowledge_lines))
    return "\n\n".join(sections)


async def handle_conversation_request(
    session: AsyncSession,
    *,
    ha_user_id: str,
    text: str,
    conversation_id: str | None,
    language: str,
    assistant_id: str | None = None,
    settings: Settings | None = None,
    model: ModelProvider | None = None,
    memory_provider: ConversationalMemoryProvider | None = None,
    knowledge_provider: KnowledgeStoreProvider | None = None,
    ha_client: HomeAssistantClient | None = None,
) -> ConversationOutcome:
    """``model``/``memory_provider``/``knowledge_provider``/``ha_client`` are injectable seams
    for tests; production callers leave them unset and this builds them from the household's
    ``ProviderSettingsRecord`` and the deployment's ``Settings``.

    ``assistant_id`` explicitly addresses an assistant other than the caller's own (ADR-002) -
    left unset, behavior is unchanged: the caller's own assistant, no access check needed. It
    only matters when starting a *new* topic; continuing an existing one always uses that
    topic's own assistant, since which assistant a topic is with is already fixed once created.
    """
    runtime_settings = settings or get_settings()
    person_id = await _resolve_person_id(session, ha_user_id=ha_user_id)
    if person_id is None:
        return Unmapped()

    topic: TopicRecord | None = None
    if conversation_id:
        topic = await _find_own_topic(session, topic_id=conversation_id, person_id=person_id)
    person = await session.get(PersonRecord, person_id)
    assert person is not None

    if topic is not None:
        assistant = await session.get(AssistantRecord, topic.assistant_id)
        assert assistant is not None, "a topic's assistant is never deleted out from under it"
    elif assistant_id is not None:
        addressed = await session.get(AssistantRecord, assistant_id)
        if addressed is None or addressed.household_id != person.household_id:
            return AssistantNotFound()
        if not can_address_assistant(
            owner_person_id=addressed.owner_person_id,
            access_mode=addressed.access_mode,
            allowed_person_ids=addressed.allowed_person_ids,
            caller_person_id=person_id,
        ):
            return AccessDenied(assistant_name=addressed.name)
        assistant = addressed
    else:
        assistant = await _find_primary_assistant(session, person_id)
        assert assistant is not None, "sync creates a primary assistant atomically with every person"

    if topic is None:
        topic = TopicRecord(
            household_id=person.household_id, person_id=person_id, assistant_id=assistant.id
        )
        session.add(topic)
        await session.flush()

    prior_turns = await _prior_turns(session, topic_id=topic.id)

    provider_settings = await get_or_create_provider_settings(session, household_id=person.household_id)
    memory = memory_provider or conversational_memory_provider(
        backend=provider_settings.memory_backend, url=provider_settings.honcho_url
    )
    knowledge = knowledge_provider or knowledge_store_provider(
        backend=provider_settings.knowledge_backend, url=provider_settings.llm_wiki_url
    )
    resolved_model = model or build_model_provider(
        provider=provider_settings.model_provider,
        base_url=provider_settings.model_base_url,
        model_name=provider_settings.model_name,
        api_key=provider_settings.model_api_key,
    )
    resolved_ha_client = ha_client or HomeAssistantClient(
        base_url=runtime_settings.home_assistant_url, token=runtime_settings.home_assistant_token
    )

    home_state: str | None = None
    if resolved_ha_client.enabled:
        home_state = _home_state_summary(await resolved_ha_client.states())

    memory_hits = await memory.recall(
        household_id=person.household_id,
        person_id=person_id,
        assistant_id=assistant.id,
        query=text,
        limit=MEMORY_RECALL_LIMIT,
    )
    knowledge_facts = await knowledge.search_facts(
        household_id=person.household_id,
        person_id=person_id,
        assistant_id=assistant.id,
        query=text,
        limit=KNOWLEDGE_SEARCH_LIMIT,
    )

    system_prompt = _build_system_prompt(
        assistant=assistant,
        person=person,
        home_state=home_state,
        memory_lines=[hit.content for hit in memory_hits],
        knowledge_lines=[f"{fact.subject} {fact.predicate}: {fact.value}" for fact in knowledge_facts],
    )
    # Interleave each stored turn's request/response as two messages, oldest first.
    history: list[ModelMessage] = []
    for turn in prior_turns:
        history.append(ModelMessage(role="user", content=turn.request_text))
        history.append(ModelMessage(role="assistant", content=turn.response_text))
    history.append(ModelMessage(role="user", content=text))

    reply = await resolved_model.generate_reply(system_prompt=system_prompt, messages=history)

    session.add(
        TopicTurnRecord(
            topic_id=topic.id,
            request_text=text,
            response_text=reply.content,
            outcome="completed",
        )
    )
    await session.flush()

    if resolved_model.name != "none":
        await memory.append_messages(
            household_id=person.household_id,
            person_id=person_id,
            assistant_id=assistant.id,
            messages=[
                ConversationMessage(role="user", content=text),
                ConversationMessage(role="assistant", content=reply.content),
            ],
        )

    return Completed(conversation_id=topic.id, response_text=reply.content)


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
