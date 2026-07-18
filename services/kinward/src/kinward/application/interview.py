from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from kinward.domain.interview import INTERVIEW_DIMENSIONS, is_skip_phrase, next_unanswered_dimension
from kinward.llm.contracts import ModelMessage, ModelProvider
from kinward.llm.providers import MODEL_UNAVAILABLE_RESPONSE, NO_MODEL_RESPONSE
from kinward.persistence.models import AssistantRecord

_DISTILL_SYSTEM_PROMPT = (
    'Summarize the user\'s answer to the question "{prompt}" as a short phrase (2-6 words) '
    "capturing their preference, in their own words where possible. Respond with ONLY the "
    "phrase - no quotes, no punctuation-only replies, no other text."
)

_ANSWER_FALLBACK_LENGTH = 120


def _fallback_value(answer_text: str) -> str:
    trimmed = answer_text.strip()[:_ANSWER_FALLBACK_LENGTH]
    return trimmed or "no preference given"


async def _distill_answer(model: ModelProvider, *, prompt: str, answer_text: str) -> str:
    """Best-effort: a degraded/unavailable model never blocks the interview turn -

    it falls back to the raw (bounded) answer text rather than losing the answer,
    matching ``application/knowledge.py``'s "never block the conversation turn" rule.
    """
    if model.name == "none":
        return _fallback_value(answer_text)
    reply = await model.generate_reply(
        system_prompt=_DISTILL_SYSTEM_PROMPT.format(prompt=prompt),
        messages=[ModelMessage(role="user", content=answer_text)],
    )
    if reply.content in (NO_MODEL_RESPONSE, MODEL_UNAVAILABLE_RESPONSE):
        return _fallback_value(answer_text)
    value = reply.content.strip().strip('"').strip("'")
    return value[:_ANSWER_FALLBACK_LENGTH] if value else _fallback_value(answer_text)


def _opening_message(dimension_prompt: str, examples: tuple[str, ...]) -> str:
    return (
        "Before we get going, I'd love to learn a bit about how you'd like me to talk with "
        'you - just a few quick questions, skip anytime by saying "skip". '
        f"{dimension_prompt} For example: {', '.join(examples)} - or just tell me in your own words."
    )


def _next_question_message(dimension_prompt: str, examples: tuple[str, ...]) -> str:
    return f"Got it. {dimension_prompt} For example: {', '.join(examples)} - or say it your own way."


async def maybe_handle_interview_turn(
    session: AsyncSession,
    model: ModelProvider,
    *,
    assistant: AssistantRecord,
    person_id: str,
    text: str,
) -> str | None:
    """If this turn belongs to Story 3.5's personality interview, handle it and return the

    reply text; otherwise return ``None`` so the caller falls through to the normal
    conversation pipeline. Never triggers for an assistant that isn't the caller's own -
    the interview is about *your* assistant, never one you merely have access to.
    """
    if assistant.owner_person_id != person_id:
        return None

    if assistant.interview_state == "not_started":
        assistant.interview_state = "in_progress"
        assistant.record_version += 1
        await session.flush()
        first = INTERVIEW_DIMENSIONS[0]
        return _opening_message(first.prompt, first.examples)

    if assistant.interview_state != "in_progress":
        return None

    if is_skip_phrase(text):
        assistant.interview_state = "skipped"
        assistant.record_version += 1
        await session.flush()
        return "No problem - I'll go with a sensible default for now. You can always redo this later."

    question = next_unanswered_dimension(assistant.personality)
    if question is None:
        # Every dimension already answered (e.g. a Story 3.6 import landed mid-interview) -
        # complete rather than asking a question that no longer exists.
        assistant.interview_state = "completed"
        assistant.record_version += 1
        await session.flush()
        return None

    value = await _distill_answer(model, prompt=question.prompt, answer_text=text)
    personality = dict(assistant.personality)
    personality[question.dimension] = value
    assistant.personality = personality

    next_question = next_unanswered_dimension(personality)
    if next_question is None:
        assistant.interview_state = "completed"
        assistant.record_version += 1
        await session.flush()
        return "Got it - thanks! I'll talk with you that way from now on. What can I help you with?"

    assistant.record_version += 1
    await session.flush()
    return _next_question_message(next_question.prompt, next_question.examples)
