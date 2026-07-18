from __future__ import annotations

from kinward.application.visual_packs import DEFAULT_VISUAL_PACK_ID, get_visual_pack, list_visual_packs
from kinward.domain.visual_packs import VisualPack, VisualPackStage, stage_for


def test_default_pack_is_registered() -> None:
    assert get_visual_pack(DEFAULT_VISUAL_PACK_ID) is not None


def test_built_in_packs_cover_multiple_categories() -> None:
    packs = list_visual_packs()
    ids = {pack.id for pack in packs}
    assert {"orb", "robot", "dog", "portrait"} <= ids
    categories = {pack.category for pack in packs}
    assert len(categories) > 1, "the catalog must not hardcode a single shape/category"
    for pack in packs:
        assert len(pack.stages) >= 2


def test_unknown_pack_id_returns_none() -> None:
    assert get_visual_pack("does-not-exist") is None


def _pack(*, stage_count: int) -> VisualPack:
    return VisualPack(
        id="test-pack",
        display_name="Test Pack",
        category="abstract",
        default_accent="#000000",
        stages=tuple(
            VisualPackStage(name=f"stage-{i}", mdi_icon="mdi:circle") for i in range(stage_count)
        ),
    )


def test_stage_for_not_started_is_first_stage() -> None:
    pack = _pack(stage_count=3)
    stage = stage_for(pack, interview_state="not_started", personality={})
    assert stage.name == "stage-0"


def test_stage_for_completed_is_last_stage_even_with_empty_personality() -> None:
    pack = _pack(stage_count=3)
    stage = stage_for(pack, interview_state="completed", personality={})
    assert stage.name == "stage-2"


def test_stage_for_skipped_is_last_stage() -> None:
    pack = _pack(stage_count=3)
    stage = stage_for(pack, interview_state="skipped", personality={})
    assert stage.name == "stage-2"


def test_stage_for_in_progress_interpolates_by_answered_ratio() -> None:
    pack = _pack(stage_count=3)
    zero_answered = stage_for(pack, interview_state="in_progress", personality={})
    assert zero_answered.name == "stage-0"

    all_five_answered = stage_for(
        pack,
        interview_state="in_progress",
        personality={
            "communication_style": "x",
            "urgency_handling": "x",
            "humor_warmth": "x",
            "formality_register": "x",
            "response_length": "x",
        },
    )
    assert all_five_answered.name == "stage-2"


def test_stage_for_single_stage_pack_never_indexes_out_of_range() -> None:
    pack = _pack(stage_count=1)
    for state in ("not_started", "in_progress", "completed", "skipped"):
        assert stage_for(pack, interview_state=state, personality={}).name == "stage-0"
