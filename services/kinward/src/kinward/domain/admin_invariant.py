from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AdminInvariantViolation:
    code: str
    message: str


def validate_admin_removal(
    *, admin_count_before: int, person_being_removed_is_admin: bool
) -> tuple[Literal[True], None] | tuple[None, AdminInvariantViolation]:
    """Enforce that the household never ends up with zero administrators.

    Kinward derives admin role live from HA's own admin flag on every sync pass
    (see ``people_sync.sync_people``), so any number of simultaneous admins is
    normal and expected - there is no single distinguished "sole administrator"
    to protect. The invariant that survives that redesign is narrower: removing
    a person must never leave the household with none at all.
    """
    if person_being_removed_is_admin and admin_count_before <= 1:
        return None, AdminInvariantViolation(
            code="household_requires_an_admin",
            message="At least one household administrator must remain.",
        )
    return True, None
