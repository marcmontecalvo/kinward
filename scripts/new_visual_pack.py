#!/usr/bin/env python3
"""Scaffold a new Epic 3 Story 3.7 visual pack manifest.

Usage:
    uv run --project services/kinward python scripts/new_visual_pack.py <id> \\
        --display-name "Dog" --category animal [--accent "#D98E4A"] \\
        [--stage napping:mdi:sleep --stage getting_acquainted:mdi:paw --stage companion:mdi:dog-side]

Also reachable as `make new-visual-pack NAME=<id> DISPLAY_NAME="..." CATEGORY=...`.

Writes services/kinward/src/kinward/visual_packs/<id>.json. The catalog loader
(kinward.application.visual_packs.list_visual_packs) picks it up automatically
on next import - adding a pack is authoring this one file, never a code change
to the loader, the API, or any renderer that reads the catalog.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKS_DIR = Path(__file__).resolve().parents[1] / "services/kinward/src/kinward/visual_packs"

DEFAULT_STAGES = [
    "unformed:mdi:help-circle-outline",
    "forming:mdi:progress-question",
    "formed:mdi:check-circle-outline",
]


def _parse_stage(raw: str) -> dict[str, str]:
    name, separator, mdi_icon = raw.partition(":")
    if not separator or not name or not mdi_icon:
        raise argparse.ArgumentTypeError(
            f"stage {raw!r} must be 'name:mdi:icon-name' (e.g. 'quiet:mdi:circle-outline')"
        )
    return {"name": name, "mdi_icon": mdi_icon}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new visual pack manifest (Epic 3 Story 3.7)."
    )
    parser.add_argument("id", help="Pack id, e.g. 'dog' - used as the filename and API id.")
    parser.add_argument("--display-name", required=True, help="Human-readable name, e.g. 'Dog'.")
    parser.add_argument("--category", required=True, help="Free-form category, e.g. 'animal'.")
    parser.add_argument("--accent", default="#6C63FF", help="Default hex accent color.")
    parser.add_argument(
        "--stage",
        dest="stages",
        action="append",
        metavar="NAME:MDI_ICON",
        help=(
            "Repeatable. A lifecycle stage as 'name:mdi:icon-name', in order. "
            "Defaults to a generic 3-stage unformed/forming/formed set."
        ),
    )
    args = parser.parse_args(argv)

    pack_id = args.id.strip().lower()
    if not pack_id or not all(c.isalnum() or c in "-_" for c in pack_id):
        print(
            f"error: {pack_id!r} is not a valid pack id (use lowercase letters/digits/-/_).",
            file=sys.stderr,
        )
        return 2

    target = PACKS_DIR / f"{pack_id}.json"
    if target.exists():
        print(f"error: {target} already exists.", file=sys.stderr)
        return 2

    raw_stages = args.stages or DEFAULT_STAGES
    try:
        stages = [_parse_stage(raw) for raw in raw_stages]
    except argparse.ArgumentTypeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    manifest = {
        "id": pack_id,
        "display_name": args.display_name,
        "category": args.category,
        "default_accent": args.accent,
        "stages": stages,
    }
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
    print(
        "No other code change needed - "
        "kinward.application.visual_packs.list_visual_packs() picks it up automatically."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
