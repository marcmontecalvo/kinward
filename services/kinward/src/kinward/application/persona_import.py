from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.assistants import AssistantNotFound
from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.domain.interview import INTERVIEW_DIMENSIONS, next_unanswered_dimension
from kinward.llm.contracts import ModelMessage, ModelProvider
from kinward.persistence.models import AssistantRecord

MAX_IMPORT_DOCUMENT_LENGTH = 20_000
MAX_GROUNDING_NOTES_LENGTH = 2_000
MAX_DIMENSION_VALUE_LENGTH = 120

_DIMENSION_NAMES = frozenset(question.dimension for question in INTERVIEW_DIMENSIONS)

_EXTRACTION_SYSTEM_PROMPT = """You read an existing AI-assistant persona document (a "soul.md", an \
AGENTS.md-style character file, or a similar system-prompt/character description from another AI \
project) and map whatever it says onto a fixed set of interaction dimensions for a household \
assistant named {assistant_name}.

Dimensions (use exactly these keys, only if the document actually addresses them - omit any dimension \
it doesn't speak to): {dimension_list}.

Respond with ONLY a JSON object, no other text, matching this shape:
{{"dimensions": {{"<dimension>": "<short phrase, 2-8 words>", ...}}, "grounding_notes": "<free text, \
up to 500 words, covering backstory, voice, catchphrases, or anything else worth keeping that doesn't \
fit a dimension - empty string if nothing applies>"}}

Never invent a preference the document doesn't support. If the document is empty, off-topic, or \
unusable, respond with {{"dimensions": {{}}, "grounding_notes": ""}}."""


@dataclass(frozen=True)
class PersonaImportProposal:
    """Never applied automatically - the caller always routes this through owner review

    (``apply_persona_import``) before anything reaches ``AssistantRecord.personality``.
    """

    dimensions: dict[str, str] = field(default_factory=dict)
    grounding_notes: str = ""


def _parse_proposal(raw: str) -> PersonaImportProposal:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return PersonaImportProposal()
    if not isinstance(payload, dict):
        return PersonaImportProposal()

    dimensions: dict[str, str] = {}
    raw_dimensions = payload.get("dimensions")
    if isinstance(raw_dimensions, dict):
        for key, value in raw_dimensions.items():
            if key in _DIMENSION_NAMES and isinstance(value, str) and value.strip():
                dimensions[key] = value.strip()[:MAX_DIMENSION_VALUE_LENGTH]

    raw_notes = payload.get("grounding_notes")
    notes = raw_notes.strip()[:MAX_GROUNDING_NOTES_LENGTH] if isinstance(raw_notes, str) else ""
    return PersonaImportProposal(dimensions=dimensions, grounding_notes=notes)


async def extract_persona_document(
    model: ModelProvider, *, assistant_name: str, document_text: str
) -> PersonaImportProposal:
    """Best-effort: an unavailable/degraded model yields an empty proposal, never an error -

    matches ``knowledge.extract_candidate_observations``'s "a bad or unavailable extraction
    call must never block" rule. Purely advisory: nothing here touches the database.
    """
    if model.name == "none":
        return PersonaImportProposal()
    reply = await model.generate_reply(
        system_prompt=_EXTRACTION_SYSTEM_PROMPT.format(
            assistant_name=assistant_name, dimension_list=", ".join(sorted(_DIMENSION_NAMES))
        ),
        messages=[ModelMessage(role="user", content=document_text[:MAX_IMPORT_DOCUMENT_LENGTH])],
    )
    return _parse_proposal(reply.content)


async def apply_persona_import(
    session: AsyncSession,
    *,
    ha_user_id: str,
    assistant_id: str,
    dimensions: dict[str, str],
    grounding_notes: str,
) -> AssistantRecord | AssistantNotFound | Unmapped:
    """Commit an owner-confirmed (possibly hand-edited) proposal - never the raw extraction.

    Not mutually exclusive with the conversational interview (Story 3.5) in either order:
    dimensions this import didn't cover stay unanswered, so the interview picks up exactly
    where the import left off next time it runs; state only advances to "completed" once
    every dimension is actually filled.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistant = await session.get(AssistantRecord, assistant_id)
    if assistant is None or assistant.owner_person_id != person.id:
        return AssistantNotFound()

    personality = dict(assistant.personality)
    for key, value in dimensions.items():
        if key in _DIMENSION_NAMES and value.strip():
            personality[key] = value.strip()[:MAX_DIMENSION_VALUE_LENGTH]
    if grounding_notes.strip():
        personality["grounding_notes"] = grounding_notes.strip()[:MAX_GROUNDING_NOTES_LENGTH]
    assistant.personality = personality

    if next_unanswered_dimension(personality) is None:
        assistant.interview_state = "completed"
    elif assistant.interview_state == "not_started":
        assistant.interview_state = "in_progress"
    assistant.record_version += 1
    await session.flush()
    return assistant
