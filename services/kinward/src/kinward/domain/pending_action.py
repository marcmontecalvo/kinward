from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

RESOLVABLE_STATE = "pending"


@dataclass(frozen=True)
class ApprovalResolutionError:
    code: str
    message: str


def can_resolve_approval(
    *, state: str, resolver_is_admin: bool, expires_at: datetime, now: datetime
) -> tuple[Literal[True], None] | tuple[None, ApprovalResolutionError]:
    """Whether an approve/deny decision may be recorded right now (ADR-002 sec. 5).

    Only a household administrator may resolve a pending action - there is no
    per-resource ``affected_person_id`` to notify for the HA device-control case
    this pass builds (unlike ADR-002's calendar-reschedule example), so "any
    current admin" is the approver, mirroring cross-cutting rule 4's plural-admin
    model. A resolution attempt past ``expires_at`` is rejected here rather than
    silently accepted - the caller is expected to transition the record to
    ``expired`` separately, since discovering expiry is not itself a resolution.
    """
    if not resolver_is_admin:
        return None, ApprovalResolutionError(
            code="admin_required", message="Only a household administrator may resolve this."
        )
    if now >= expires_at:
        return None, ApprovalResolutionError(
            code="expired", message="This pending action has expired."
        )
    if state != RESOLVABLE_STATE:
        return None, ApprovalResolutionError(
            code="not_pending", message=f"This pending action is already {state}."
        )
    return True, None


def can_cancel_approval(
    *, state: str, requester_is_owner: bool, expires_at: datetime, now: datetime
) -> tuple[Literal[True], None] | tuple[None, ApprovalResolutionError]:
    """Whether the original requester may withdraw their own still-pending action.

    ADR-002's ``cancelled`` state has been part of the enum since migration
    ``010_meaningful_action_approvals`` but had no producer until this (Epic 6
    Story 6.1's remaining gap). Only the person who requested the action may
    cancel it - not an admin, not another household member. Approving/denying is
    the admin's decision (``can_resolve_approval`` above); cancelling is the
    requester's own retraction of a request nobody has acted on yet. Expiry and
    already-resolved checks mirror ``can_resolve_approval`` for the same reasons.
    """
    if not requester_is_owner:
        return None, ApprovalResolutionError(
            code="not_requester",
            message="Only the person who requested this action may cancel it.",
        )
    if now >= expires_at:
        return None, ApprovalResolutionError(
            code="expired", message="This pending action has expired."
        )
    if state != RESOLVABLE_STATE:
        return None, ApprovalResolutionError(
            code="not_pending", message=f"This pending action is already {state}."
        )
    return True, None


def revalidate_before_execution(
    *, state: str, expires_at: datetime, now: datetime
) -> tuple[Literal[True], None] | tuple[None, ApprovalResolutionError]:
    """Re-check immediately before executing an approved action (AD-20's
    re-check-at-execution-time rule; ADR-002 sec. 5's five re-validation conditions,
    narrowed to what this v0 slice tracks: approval still valid, not expired).
    """
    if now >= expires_at:
        return None, ApprovalResolutionError(
            code="expired", message="This pending action expired before it could execute."
        )
    if state != "approved":
        return None, ApprovalResolutionError(
            code="not_approved", message=f"This pending action is {state}, not approved."
        )
    return True, None
