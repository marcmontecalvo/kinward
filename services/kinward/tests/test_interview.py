from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.interview import maybe_handle_interview_turn
from kinward.domain.interview import INTERVIEW_DIMENSIONS, is_skip_phrase, next_unanswered_dimension
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.persistence.models import AssistantRecord, Base, HouseholdRecord, PersonRecord


class _StubModel:
    name = "stub"

    def __init__(self, reply_text: str = "distilled answer") -> None:
        self.reply_text = reply_text
        self.calls: list[Sequence[ModelMessage]] = []

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        self.calls.append(messages)
        return ModelReply(content=self.reply_text)


@dataclass(frozen=True)
class _NoneModel:
    name: str = "none"

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        raise AssertionError("the none model must never be called for distillation")


def test_next_unanswered_dimension_follows_fixed_order() -> None:
    first = next_unanswered_dimension({})
    assert first is not None
    assert first.dimension == INTERVIEW_DIMENSIONS[0].dimension

    skipping_first = next_unanswered_dimension({INTERVIEW_DIMENSIONS[0].dimension: "x"})
    assert skipping_first is not None
    assert skipping_first.dimension == INTERVIEW_DIMENSIONS[1].dimension


def test_next_unanswered_dimension_is_none_when_all_answered() -> None:
    personality = {question.dimension: "x" for question in INTERVIEW_DIMENSIONS}
    assert next_unanswered_dimension(personality) is None


def test_manually_set_dimension_counts_as_answered() -> None:
    manual = {INTERVIEW_DIMENSIONS[0].dimension: "set via direct API edit, not the interview"}
    result = next_unanswered_dimension(manual)
    assert result is not None
    assert result.dimension == INTERVIEW_DIMENSIONS[1].dimension


def test_is_skip_phrase_deterministic() -> None:
    assert is_skip_phrase("skip")
    assert is_skip_phrase("Can we do this later?")
    assert not is_skip_phrase("I'm direct and to the point")


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_not_started_assistant(session):  # type: ignore[no-untyped-def]
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


async def test_first_turn_opens_the_interview_without_consuming_the_models_reply() -> None:
    factory = await _factory()
    async with factory() as session:
        person, assistant = await _seed_not_started_assistant(session)
        model = _StubModel()

        reply = await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="hi"
        )

        assert reply is not None
        assert INTERVIEW_DIMENSIONS[0].prompt in reply
        assert assistant.interview_state == "in_progress"
        assert model.calls == [], "the opening turn must not call the model - it's deterministic"


async def test_answering_a_question_advances_to_the_next_dimension() -> None:
    factory = await _factory()
    async with factory() as session:
        person, assistant = await _seed_not_started_assistant(session)
        model = _StubModel(reply_text="Direct")
        await maybe_handle_interview_turn(session, model, assistant=assistant, person_id=person.id, text="hi")

        reply = await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="I like it direct"
        )

        assert reply is not None
        assert INTERVIEW_DIMENSIONS[1].prompt in reply
        assert assistant.personality[INTERVIEW_DIMENSIONS[0].dimension] == "Direct"
        assert assistant.interview_state == "in_progress"


async def test_completing_every_dimension_marks_interview_completed() -> None:
    factory = await _factory()
    async with factory() as session:
        person, assistant = await _seed_not_started_assistant(session)
        model = _StubModel(reply_text="answer")
        await maybe_handle_interview_turn(session, model, assistant=assistant, person_id=person.id, text="hi")
        for _ in range(len(INTERVIEW_DIMENSIONS) - 1):
            await maybe_handle_interview_turn(
                session, model, assistant=assistant, person_id=person.id, text="answer"
            )
        final_reply = await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="answer"
        )

        assert final_reply is not None
        assert assistant.interview_state == "completed"
        assert len(assistant.personality) == len(INTERVIEW_DIMENSIONS)

        # Once completed, this stops handling turns at all.
        after_completion = await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="anything"
        )
        assert after_completion is None


async def test_skip_phrase_ends_the_interview_deterministically_without_a_model_call() -> None:
    factory = await _factory()
    async with factory() as session:
        person, assistant = await _seed_not_started_assistant(session)
        model = _NoneModel()
        await maybe_handle_interview_turn(session, model, assistant=assistant, person_id=person.id, text="hi")

        reply = await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="skip please"
        )

        assert reply is not None
        assert assistant.interview_state == "skipped"


async def test_degraded_model_falls_back_to_raw_answer_text() -> None:
    factory = await _factory()
    async with factory() as session:
        person, assistant = await _seed_not_started_assistant(session)
        model = _NoneModel()
        await maybe_handle_interview_turn(session, model, assistant=assistant, person_id=person.id, text="hi")

        await maybe_handle_interview_turn(
            session, model, assistant=assistant, person_id=person.id, text="I like it short and direct"
        )

        assert assistant.personality[INTERVIEW_DIMENSIONS[0].dimension] == "I like it short and direct"


async def test_completed_assistant_never_enters_the_interview() -> None:
    factory = await _factory()
    async with factory() as session:
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
            household_id=household.id, owner_person_id=person.id, name="Marc's Assistant", kind="primary"
        )
        session.add(assistant)
        await session.flush()

        reply = await maybe_handle_interview_turn(
            session, _StubModel(), assistant=assistant, person_id=person.id, text="hello"
        )

        assert reply is None


async def test_interview_never_triggers_for_someone_elses_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        _owner, assistant = await _seed_not_started_assistant(session)

        reply = await maybe_handle_interview_turn(
            session, _StubModel(), assistant=assistant, person_id="someone-else", text="hello"
        )

        assert reply is None
        assert assistant.interview_state == "not_started"
