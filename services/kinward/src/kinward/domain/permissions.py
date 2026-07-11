from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

ChildEditPolicy = Literal["open", "approval-required", "admin-only"]


@dataclass(frozen=True)
class PermissionDenied:
    code: str
    message: str


def enforce_child_self_edit(
    *, policy: ChildEditPolicy, is_child: bool
) -> tuple[Literal[True], None] | tuple[None, PermissionDenied]:
    """Return whether a child may change their own assistant settings.

    The retained rule is intentionally simple: adults are always allowed,
    children are allowed under open, require approval under approval-required,
    and are blocked under admin-only.
    """
    if not is_child or policy == "open":
        return True, None
    if policy == "approval-required":
        return None, PermissionDenied(
            code="child_self_edit_approval_required",
            message="An adult administrator must approve this change.",
        )
    return None, PermissionDenied(
        code="child_self_edit_not_allowed",
        message="Household settings do not allow this change.",
    )


def is_child(*, role: str, age_years: int | None) -> bool:
    if role == "child":
        return True
    if role in {"admin", "adult", "teen"}:
        return False
    return age_years is None or age_years < 13


def require_owner(
    *, person_id: str, memberships: Sequence[object]
) -> tuple[Literal[True], None] | tuple[None, PermissionDenied]:
    for membership in memberships:
        if (
            getattr(membership, "person_id", None) == person_id
            and getattr(membership, "role", None) == "owner"
        ):
            return True, None
    return None, PermissionDenied(
        code="assistant_owner_required",
        message="Assistant ownership is required for this operation.",
    )
