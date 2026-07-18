from __future__ import annotations

from dataclasses import dataclass

_SKIP_PHRASES = (
    "skip",
    "ask me later",
    "not now",
    "maybe later",
    "later",
    "no thanks",
)


@dataclass(frozen=True)
class InterviewQuestion:
    dimension: str
    prompt: str
    examples: tuple[str, ...]


INTERVIEW_DIMENSIONS: tuple[InterviewQuestion, ...] = (
    InterviewQuestion(
        dimension="communication_style",
        prompt="How would you like me to talk with you day to day?",
        examples=("Direct", "Diplomatic", "Playful"),
    ),
    InterviewQuestion(
        dimension="urgency_handling",
        prompt="When something's time-sensitive, how pushy should I be about it?",
        examples=("Nudge me gently", "Be direct and immediate", "Just tell me once"),
    ),
    InterviewQuestion(
        dimension="humor_warmth",
        prompt="Should I keep things light and warm, or stay more businesslike?",
        examples=("Warm and a little playful", "Friendly but focused", "Strictly businesslike"),
    ),
    InterviewQuestion(
        dimension="formality_register",
        prompt="How formal or casual should I sound?",
        examples=("Casual, like a friend", "Polite and professional", "Somewhere in between"),
    ),
    InterviewQuestion(
        dimension="response_length",
        prompt="Do you prefer short answers, or more detail and context?",
        examples=("Short and to the point", "Give me the full picture", "Depends on the topic"),
    ),
)

_DIMENSIONS_BY_NAME = {question.dimension: question for question in INTERVIEW_DIMENSIONS}


def next_unanswered_dimension(personality: dict[str, object]) -> InterviewQuestion | None:
    """The first interview dimension not yet present in ``personality``, in a fixed order.

    A manually-set ``personality`` key (via direct API edit, not the interview) still
    counts as "answered" - the interview never overwrites a preference someone already
    set some other way (e.g. a Story 3.6 import).
    """
    for question in INTERVIEW_DIMENSIONS:
        if question.dimension not in personality:
            return question
    return None


def is_skip_phrase(text: str) -> bool:
    """Deterministic, LLM-free skip detection - no model call needed to recognize "skip"."""
    lowered = text.strip().lower()
    return any(phrase in lowered for phrase in _SKIP_PHRASES)
