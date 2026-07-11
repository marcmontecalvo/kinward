from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

AssistantType = Literal["personal", "shared-fallback"]


@dataclass(frozen=True)
class OwnershipViolation:
    code: str
    message: str


def validate_owner_count(
    *, assistant_type: AssistantType, owner_count: int
) -> tuple[Literal[True], None] | tuple[None, OwnershipViolation]:
    """Enforce the retained assistant ownership invariants.

    Personal assistants have exactly one owner. The shared fallback assistant is
    household-scoped and therefore has no personal owners.
    """
    if assistant_type == "personal" and owner_count != 1:
        return None, OwnershipViolation(
            code="personal_assistant_owner_count",
            message=f"Personal assistant must have exactly 1 owner, found {owner_count}.",
        )

    if assistant_type == "shared-fallback" and owner_count != 0:
        return None, OwnershipViolation(
            code="shared_fallback_owner_count",
            message=f"Shared fallback assistant must have no personal owners, found {owner_count}.",
        )

    return True, None


def count_owners(memberships: Sequence[object]) -> int:
    return sum(1 for membership in memberships if getattr(membership, "role", None) == "owner")
