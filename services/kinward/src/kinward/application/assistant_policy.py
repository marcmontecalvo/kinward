from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import AssistantPolicyRecord


class _Unset:
    """Distinguishes "field not passed" from an explicit ``None`` (clear the cap)."""


_UNSET = _Unset()


async def get_or_create_assistant_policy(
    session: AsyncSession, *, household_id: str
) -> AssistantPolicyRecord:
    """Every household gets exactly one row, created lazily on first access.

    Defaults to no cap and no approval gate - today's "just create it" behavior
    is unchanged until an admin explicitly restricts it.
    """
    policy = await session.scalar(
        select(AssistantPolicyRecord).where(AssistantPolicyRecord.household_id == household_id)
    )
    if policy is not None:
        return policy
    policy = AssistantPolicyRecord(household_id=household_id)
    session.add(policy)
    await session.flush()
    return policy


async def update_assistant_policy(
    session: AsyncSession,
    *,
    household_id: str,
    max_assistants_per_person: int | None | _Unset = _UNSET,
    require_admin_approval_for_creation: bool | None = None,
) -> AssistantPolicyRecord:
    """Partial update: a field left unpassed is left unchanged.

    ``max_assistants_per_person`` is itself nullable (``None`` means "no cap"), so it
    uses the ``_UNSET`` sentinel default to distinguish "not passed" from "explicitly
    clearing the cap".
    """
    policy = await get_or_create_assistant_policy(session, household_id=household_id)
    if not isinstance(max_assistants_per_person, _Unset):
        policy.max_assistants_per_person = max_assistants_per_person
    if require_admin_approval_for_creation is not None:
        policy.require_admin_approval_for_creation = require_admin_approval_for_creation
    policy.record_version += 1
    await session.flush()
    return policy
