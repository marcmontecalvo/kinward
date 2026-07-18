from __future__ import annotations

from dataclasses import dataclass

from kinward.domain.interview import INTERVIEW_DIMENSIONS


@dataclass(frozen=True)
class VisualPackStage:
    name: str
    mdi_icon: str
    preview_image: str | None = None


@dataclass(frozen=True)
class VisualPack:
    """A catalog entry (Epic 3 Story 3.7) - never a hardcoded shape.

    ``stages`` is an ordered, pack-chosen set of names generic to any visual metaphor
    (never orb-specific terms baked in here) - an orb might call them
    quiet/active/speaking, a Tamagotchi-style pack might call them egg/hatchling/grown.
    Only their position in the sequence carries meaning to ``stage_for``.
    """

    id: str
    display_name: str
    category: str
    default_accent: str
    stages: tuple[VisualPackStage, ...]


def stage_for(pack: VisualPack, *, interview_state: str, personality: dict[str, object]) -> VisualPackStage:
    """Which of a pack's stages an assistant is currently in.

    Derived, never persisted separately - "not started" is always the pack's first
    stage, "completed"/"skipped" is always its last, and "in progress" interpolates by
    how many of the fixed interview dimensions (Story 3.5) are already answered in
    ``personality`` - the same answered/total ratio idea Homefront's own orb used,
    generalized to work for a pack of any length.
    """
    if not pack.stages:
        raise ValueError(f"visual pack {pack.id!r} has no stages")
    if interview_state in ("completed", "skipped"):
        return pack.stages[-1]
    if interview_state != "in_progress":
        return pack.stages[0]
    total = len(INTERVIEW_DIMENSIONS)
    answered = sum(1 for question in INTERVIEW_DIMENSIONS if question.dimension in personality)
    ratio = answered / total if total else 0.0
    index = min(len(pack.stages) - 1, int(ratio * len(pack.stages)))
    return pack.stages[index]
