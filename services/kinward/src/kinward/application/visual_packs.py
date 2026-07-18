from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

from kinward.domain.visual_packs import VisualPack, VisualPackStage

DEFAULT_VISUAL_PACK_ID = "orb"

_PACKAGE = "kinward.visual_packs"


def _parse_pack(data: dict[str, Any]) -> VisualPack:
    stages = tuple(
        VisualPackStage(
            name=stage["name"],
            mdi_icon=stage["mdi_icon"],
            preview_image=stage.get("preview_image"),
        )
        for stage in data["stages"]
    )
    return VisualPack(
        id=data["id"],
        display_name=data["display_name"],
        category=data["category"],
        default_accent=data["default_accent"],
        stages=stages,
    )


@lru_cache(maxsize=1)
def list_visual_packs() -> tuple[VisualPack, ...]:
    """Every built-in pack, loaded once from the ``kinward.visual_packs`` package data.

    Adding a new pack is dropping a new ``<id>.json`` file into that package (see
    ``scripts/new_visual_pack.py``) - this loader never needs a code change.
    """
    packs: list[VisualPack] = []
    for entry in resources.files(_PACKAGE).iterdir():
        if not entry.name.endswith(".json"):
            continue
        data = json.loads(entry.read_text(encoding="utf-8"))
        packs.append(_parse_pack(data))
    return tuple(sorted(packs, key=lambda pack: pack.id))


def get_visual_pack(pack_id: str) -> VisualPack | None:
    for pack in list_visual_packs():
        if pack.id == pack_id:
            return pack
    return None


def visual_pack_ids() -> frozenset[str]:
    return frozenset(pack.id for pack in list_visual_packs())
