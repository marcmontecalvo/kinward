from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.interview import maybe_handle_interview_turn
from kinward.application.operational_context import (
    EntityResolution,
    ResolvedEntity,
    resolve_recent_device,
    resolve_recent_timer,
)
from kinward.application.provider_settings import get_or_create_provider_settings
from kinward.application.resource_labels import get_resource_label_overrides
from kinward.config import Settings, get_settings
from kinward.domain.assistant_access import can_address_assistant
from kinward.domain.ha_observation import ObservedState, is_current, observe_states
from kinward.domain.household_resource_labels import resolve_label
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


LabelResolver = Callable[[str], str]


def _home_state_summary(
    observed_states: list[ObservedState], *, now: datetime, label_for: LabelResolver
) -> str | None:
    """Household-language entity/state lines for the model's grounding context - current
    entities only (Story 7.1: "ordinary outputs use household language").

    An entity that is unavailable or whose observation has gone stale (Story 7.2: "unavailable
    or stale state cannot be represented as current") is left out of the summary rather than
    reported with a possibly-misleading state value; the omission count is surfaced instead so
    the assistant can honestly say it can't see something rather than staying silent about it.
    """
    lines: list[str] = []
    omitted = 0
    for observed in observed_states:
        if not is_current(observed, now=now):
            omitted += 1
            continue
        lines.append(f"{label_for(observed.entity_id)}: {observed.state}")
    if not lines and not omitted:
        return None
    lines.sort()
    summary = "\n".join(lines[:MAX_HOME_STATE_ENTITIES])
    if omitted:
        note = f"({omitted} additional entities omitted: unavailable or state not currently fresh.)"
        summary = f"{summary}\n{note}" if summary else note
    return summary


def _recent_reference_note(
    recent_device: EntityResolution, recent_timer: EntityResolution, *, label_for: LabelResolver
) -> str | None:
    lines: list[str] = []
    if isinstance(recent_device, ResolvedEntity):
        lines.append(
            f"Most recently changed light/switch: {label_for(recent_device.entity_id)} is "
            f"{recent_device.state} (changed {recent_device.last_changed})."
        )
    if isinstance(recent_timer, ResolvedEntity):
        lines.append(f"Currently active timer: {label_for(recent_timer.entity_id)}.")
    if not lines:
        return None
    return "\n".join(lines)


def _build_system_prompt(
    *,
    assistant: AssistantRecord,
    person: PersonRecord,
    home_state: str | None,
    recent_reference_note: str | None,
    briefing_text: str | None,
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
    if recent_reference_note:
        sections.append(recent_reference_note)
    if briefing_text:
        sections.append(
            "Current calendar briefing (Epic 5 - summarize only this; never invent "
            "conflicts or importance beyond what it states):\n" + briefing_text
        )
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
    device_id: str | None = None,
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

    ``device_id`` is the HA device that heard this request, forwarded so recent-reference
    resolution (ADR-002 sec. 3's v0 heuristic - see ``application/operational_context.py``) can
    prefer the caller's current area. It plays no role beyond that.
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

    # Epic 3 Story 3.5: a not-started/in-progress personality interview owns this turn
    # entirely - short-circuits before touching HA state, calendar, memory, or knowledge,
    # since none of that is relevant to "how would you like me to talk with you?".
    interview_reply = await maybe_handle_interview_turn(
        session, resolved_model, assistant=assistant, person_id=person_id, text=text
    )
    if interview_reply is not None:
        session.add(
            TopicTurnRecord(
                topic_id=topic.id, request_text=text, response_text=interview_reply, outcome="completed"
            )
        )
        await session.flush()
        return Completed(conversation_id=topic.id, response_text=interview_reply)

    resolved_ha_client = ha_client or HomeAssistantClient(
        base_url=runtime_settings.home_assistant_url, token=runtime_settings.home_assistant_token
    )

    home_state: str | None = None
    recent_reference_note: str | None = None
    if resolved_ha_client.enabled:
        home_state_raw = await resolved_ha_client.states()
        observed_at = datetime.now(timezone.utc)
        observed_states = observe_states(home_state_raw, observed_at=observed_at)
        label_overrides = await get_resource_label_overrides(
            session, household_id=person.household_id
        )
        attributes_by_entity = {observed.entity_id: observed.attributes for observed in observed_states}

        def label_for(entity_id: str) -> str:
            return resolve_label(
                entity_id,
                override=label_overrides.get(entity_id),
                attributes=attributes_by_entity.get(entity_id),
            )

        home_state = _home_state_summary(observed_states, now=observed_at, label_for=label_for)
        recent_device = await resolve_recent_device(
            resolved_ha_client, states=home_state_raw, device_id=device_id
        )
        recent_timer = await resolve_recent_timer(
            resolved_ha_client, states=home_state_raw, device_id=device_id
        )
        recent_reference_note = _recent_reference_note(
            recent_device, recent_timer, label_for=label_for
        )

    # Deferred import: application.calendar (via application.briefing) imports Unmapped
    # from this module, so a top-level import here would be circular.
    from kinward.application.briefing import compute_briefing

    briefing = await compute_briefing(session, household_id=person.household_id)

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
        recent_reference_note=recent_reference_note,
        briefing_text=briefing.text_summary,
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

    if resolved_model.name != "none" and knowledge.name != "none":
        # Deferred import: application.knowledge imports Unmapped from this module, so a
        # top-level import here would be circular.
        from kinward.application.knowledge import (
            CONVERSATION_INFERENCE_SOURCE,
            extract_candidate_observations,
            propose_observation,
        )

        candidates = await extract_candidate_observations(
            resolved_model, person_display_name=person.display_name, message_text=text
        )
        for candidate in candidates:
            await propose_observation(
                session,
                knowledge,
                household_id=person.household_id,
                owner_person_id=person_id,
                assistant_id=assistant.id,
                subject=candidate.subject,
                predicate=candidate.predicate,
                value=candidate.value,
                privacy=candidate.privacy,
                source_system=CONVERSATION_INFERENCE_SOURCE,
                confidence=candidate.confidence,
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
