from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.assistants import AssistantNotFound
from kinward.application.conversation import Unmapped
from kinward.application.persona_import import apply_persona_import, extract_persona_document
from kinward.domain.interview import INTERVIEW_DIMENSIONS
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.persistence.models import AssistantRecord, Base, HouseholdRecord, PersonRecord


@dataclass
class _StubModel:
    reply_text: str
    name: str = "stub"

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        return ModelReply(content=self.reply_text)


@dataclass(frozen=True)
class _NoneModel:
    name: str = "none"

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        raise AssertionError("the none model must never be called")


async def test_extract_persona_document_parses_valid_json() -> None:
    model = _StubModel(
        reply_text='{"dimensions": {"communication_style": "Direct", "unknown_dim": "ignored"}, '
        '"grounding_notes": "Loves dry humor."}'
    )

    proposal = await extract_persona_document(model, assistant_name="Kai", document_text="some soul.md text")

    assert proposal.dimensions == {"communication_style": "Direct"}
    assert proposal.grounding_notes == "Loves dry humor."


async def test_extract_persona_document_degrades_to_empty_proposal_on_bad_json() -> None:
    model = _StubModel(reply_text="not json at all")

    proposal = await extract_persona_document(model, assistant_name="Kai", document_text="text")

    assert proposal.dimensions == {}
    assert proposal.grounding_notes == ""


async def test_extract_persona_document_never_calls_a_none_model() -> None:
    proposal = await extract_persona_document(_NoneModel(), assistant_name="Kai", document_text="text")
    assert proposal.dimensions == {}


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_owner_with_assistant(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Marc",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-marc",
        ha_user_id="ha-user-marc",
    )
    session.add(person)
    await session.flush()
    assistant = AssistantRecord(
        household_id=household.id,
        owner_person_id=person.id,
        name="Marc's Assistant",
        kind="primary",
        interview_state="not_started",
    )
    session.add(assistant)
    await session.flush()
    return person, assistant


async def test_apply_persona_import_writes_dimensions_and_grounding_notes() -> None:
    factory = await _factory()
    async with factory() as session:
        _person, assistant = await _seed_owner_with_assistant(session)

        result = await apply_persona_import(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            dimensions={"communication_style": "Direct", "not_a_real_dimension": "ignored"},
            grounding_notes="Backstory notes.",
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.personality["communication_style"] == "Direct"
        assert "not_a_real_dimension" not in result.personality
        assert result.personality["grounding_notes"] == "Backstory notes."


async def test_apply_persona_import_partial_leaves_interview_in_progress() -> None:
    factory = await _factory()
    async with factory() as session:
        _person, assistant = await _seed_owner_with_assistant(session)

        result = await apply_persona_import(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            dimensions={"communication_style": "Direct"},
            grounding_notes="",
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.interview_state == "in_progress"


async def test_apply_persona_import_complete_marks_interview_completed() -> None:
    factory = await _factory()
    async with factory() as session:
        _person, assistant = await _seed_owner_with_assistant(session)
        all_dimensions = {question.dimension: "answer" for question in INTERVIEW_DIMENSIONS}

        result = await apply_persona_import(
            session,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            dimensions=all_dimensions,
            grounding_notes="",
        )
        await session.commit()

        assert not isinstance(result, (Unmapped, AssistantNotFound))
        assert result.interview_state == "completed"


async def test_apply_persona_import_fails_closed_for_someone_elses_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        _person, assistant = await _seed_owner_with_assistant(session)

        result = await apply_persona_import(
            session,
            ha_user_id="unmapped-user",
            assistant_id=assistant.id,
            dimensions={},
            grounding_notes="",
        )

        assert isinstance(result, Unmapped)
