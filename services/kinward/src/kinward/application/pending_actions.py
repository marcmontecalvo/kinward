from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.authorization import NotAdmin, resolve_admin, resolve_person
from kinward.application.conversation import AccessDenied, AssistantNotFound, Unmapped
from kinward.config import Settings, get_settings
from kinward.domain.assistant_access import can_address_assistant
from kinward.domain.expected_state import expected_state_for
from kinward.domain.pending_action import (
    ApprovalResolutionError,
    can_cancel_approval,
    can_resolve_approval,
    revalidate_before_execution,
)
from kinward.domain.tool_permission import (
    DEFAULT_TOOL_PERMISSIONS,
    evaluate_capability,
    resolve_capability,
)
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.persistence.models import (
    ActivityRecord,
    ApprovalRecord,
    AssistantRecord,
    HomeAssistantToolPolicyRecord,
)

# ADR-002 sec. 5's worked example uses a one-day expiry; there is no per-capability
# override yet, matching the same "not a policy editor" simplicity ADR-002 sec. 4
# describes for tool permissions.
PENDING_ACTION_EXPIRY_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    """SQLite round-trips ``DateTime(timezone=True)`` values as naive - normalize

    before comparing against a freshly-constructed aware ``datetime`` (same pattern
    as ``application/bootstrap.py``'s capability expiry check).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@dataclass(frozen=True)
class InvalidTarget:
    """``entity_id`` doesn't belong to the requested HA ``domain`` - fail closed."""

    message: str


@dataclass(frozen=True)
class CapabilityDenied:
    """The household's tool policy denies this capability (or it maps to none at all)."""

    capability: str | None


@dataclass(frozen=True)
class Executed:
    pass


@dataclass(frozen=True)
class Failed:
    pass


@dataclass(frozen=True)
class PendingApprovalCreated:
    approval_id: str


@dataclass(frozen=True)
class ApprovalNotFound:
    """No such pending action, or it doesn't belong to this household - fail closed either way."""


@dataclass(frozen=True)
class Denied:
    pass


@dataclass(frozen=True)
class Cancelled:
    pass


RequestActionOutcome = (
    Unmapped
    | AssistantNotFound
    | AccessDenied
    | InvalidTarget
    | CapabilityDenied
    | Executed
    | Failed
    | PendingApprovalCreated
)

ResolveActionOutcome = (
    Unmapped | NotAdmin | ApprovalNotFound | ApprovalResolutionError | Denied | Executed | Failed
)

CancelActionOutcome = Unmapped | ApprovalNotFound | ApprovalResolutionError | Cancelled


async def get_or_create_tool_policy(
    session: AsyncSession, *, household_id: str
) -> HomeAssistantToolPolicyRecord:
    """Every household gets exactly one row, created lazily on first access and
    defaulted from ``DEFAULT_TOOL_PERMISSIONS`` - mirrors
    ``application.assistant_policy.get_or_create_assistant_policy`` exactly.
    """
    policy = await session.scalar(
        select(HomeAssistantToolPolicyRecord).where(
            HomeAssistantToolPolicyRecord.household_id == household_id
        )
    )
    if policy is not None:
        return policy
    policy = HomeAssistantToolPolicyRecord(
        household_id=household_id, permissions=dict(DEFAULT_TOOL_PERMISSIONS)
    )
    session.add(policy)
    await session.flush()
    return policy


async def update_tool_policy(
    session: AsyncSession, *, household_id: str, permissions: dict[str, str]
) -> HomeAssistantToolPolicyRecord:
    """Partial update: only the capabilities present in ``permissions`` change - any
    capability not mentioned keeps its current value rather than resetting to
    ``DEFAULT_TOOL_PERMISSIONS``. Valid ``allow``/``approval_required``/``deny``
    values are the API layer's responsibility to enforce before calling this.
    """
    policy = await get_or_create_tool_policy(session, household_id=household_id)
    policy.permissions = {**policy.permissions, **permissions}
    policy.record_version += 1
    await session.flush()
    return policy


async def _submit_and_confirm(
    ha_client: HomeAssistantClient,
    *,
    domain: str,
    service: str,
    entity_id: str,
    data: dict[str, Any] | None,
) -> tuple[Literal["executed", "failed"], Literal["completed", "failed", "unknown"], dict[str, Any]]:
    """Submit an HA service call and classify the outcome.

    ``call_service`` returning ``None`` collapses two different failure modes:
    never-attempted (disabled, circuit open - genuinely nothing happened) and
    attempted-but-response-lost (a timeout/HTTP error after the request was already
    sent - HA may have executed the action anyway). ADR-002's approval-state enum has
    no "unknown" value to hold that ambiguity, so ``ApprovalRecord.state`` resolves
    fail-closed to ``"failed"`` either way; the true ambiguity is preserved on the
    ``ActivityRecord`` (outcome ``"unknown"``, not ``"failed"``) for audit, since
    silently collapsing a possibly-successful lock/alarm call to a flat "failed"
    would be misleading (Epic 7 Story 7.3: "requested, submitted, observed, completed,
    failed, and unknown remain separate").

    For services with a deterministic expected end state (``domain/expected_state.py`` -
    e.g. ``light.turn_on`` must leave the entity ``on``), completion additionally requires a
    fresh ``get_state`` read matching that expectation - Story 7.3's "completion requires a
    fresh matching HA observation" rule. A service with no expected-state entry (e.g. any
    "toggle") keeps the older, looser rule: a non-``None`` synchronous ``call_service``
    response is sufficient evidence of completion, the same scoping discipline Story 7.2's
    read-only path used.

    An ambiguous or missing confirmation is treated exactly like the "response lost after
    send" case below: ``ApprovalRecord.state`` has no ``unknown`` value to hold the
    ambiguity, so it fail-closes to ``"failed"``, while the paired ``ActivityRecord.outcome``
    is set to ``"unknown"`` so the async reconciliation job (``worker.py``) can resolve it
    later without the household ever being told a possibly-successful action definitely
    failed. This only runs once, synchronously - it does not retry or poll; a slow HA state
    update is exactly the kind of ambiguity reconciliation exists to catch up on later.
    """
    merged: dict[str, Any] = {"entity_id": entity_id, **(data or {})}
    result = await ha_client.call_service(domain=domain, service=service, data=merged)
    detail: dict[str, Any] = {"domain": domain, "service": service, "entity_id": entity_id}
    if result is not None:
        detail["changed_states"] = len(result)
        expected_state = expected_state_for(domain=domain, service=service)
        if expected_state is None:
            return "executed", "completed", detail
        detail["expected_state"] = expected_state
        observed = await ha_client.get_state(entity_id)
        observed_state = observed.get("state") if observed else None
        detail["observed_state"] = observed_state
        if observed_state == expected_state:
            return "executed", "completed", detail
        detail["reason"] = "observation_mismatch" if observed is not None else "observation_unavailable"
        return "failed", "unknown", detail
    if not ha_client.enabled:
        detail["reason"] = "not_configured"
        return "failed", "failed", detail
    if ha_client.client.circuit_open:
        detail["reason"] = "circuit_open"
        return "failed", "failed", detail
    detail["reason"] = "ha_request_failed_after_send"
    return "failed", "unknown", detail


def _resolved_ha_client(
    *, settings: Settings | None, ha_client: HomeAssistantClient | None
) -> HomeAssistantClient:
    if ha_client is not None:
        return ha_client
    runtime_settings = settings or get_settings()
    return HomeAssistantClient(
        base_url=runtime_settings.home_assistant_url, token=runtime_settings.home_assistant_token
    )


async def request_action(
    session: AsyncSession,
    *,
    household_id: str,
    ha_user_id: str,
    assistant_id: str,
    domain: str,
    service: str,
    entity_id: str,
    data: dict[str, Any] | None,
    explanation: str,
    settings: Settings | None = None,
    ha_client: HomeAssistantClient | None = None,
) -> RequestActionOutcome:
    """Request an HA service call on behalf of the resolved caller (Epic 7 Story 7.3;
    ADR-002 sec. 4's tool-permission model).

    Capability is resolved from the actual requested ``(domain, service)`` pair, not
    a caller-asserted label (ADR-002: "must not depend on the AI deciding whether an
    operation feels appropriate") - only the codebase's ``CAPABILITY_SERVICE_ALLOWLIST``
    decides what a call is allowed to mean. There is no LLM tool-calling integration
    yet (``llm/contracts.py`` has none), so this is invoked explicitly today (HA
    service call, REST endpoint) rather than autonomously from a conversation turn -
    the same "backend capability + explicit HA service call first" precedent Story
    3.4's ``kinward.set_assistant_access`` established.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person

    assistant = await session.get(AssistantRecord, assistant_id)
    if assistant is None or assistant.household_id != household_id:
        return AssistantNotFound()
    if not can_address_assistant(
        owner_person_id=assistant.owner_person_id,
        access_mode=assistant.access_mode,
        allowed_person_ids=assistant.allowed_person_ids,
        caller_person_id=person.id,
    ):
        return AccessDenied(assistant_name=assistant.name)

    if not entity_id.startswith(f"{domain}."):
        return InvalidTarget(message=f"{entity_id!r} is not a {domain!r} entity.")

    capability = resolve_capability(domain=domain, service=service)
    policy = await get_or_create_tool_policy(session, household_id=household_id)
    permission = evaluate_capability(capability=capability, permissions=policy.permissions)

    resolved_ha_client = _resolved_ha_client(settings=settings, ha_client=ha_client)

    if permission == "deny":
        session.add(
            ActivityRecord(
                household_id=household_id,
                assistant_id=assistant.id,
                person_id=person.id,
                summary=f"Denied {domain}.{service} on {entity_id}",
                outcome="denied",
                detail={"domain": domain, "service": service, "entity_id": entity_id, "capability": capability},
            )
        )
        await session.flush()
        return CapabilityDenied(capability=capability)

    if permission == "allow":
        approval_state, activity_outcome, detail = await _submit_and_confirm(
            resolved_ha_client, domain=domain, service=service, entity_id=entity_id, data=data
        )
        session.add(
            ActivityRecord(
                household_id=household_id,
                assistant_id=assistant.id,
                person_id=person.id,
                summary=f"{domain}.{service} on {entity_id}",
                outcome=activity_outcome,
                detail=detail,
            )
        )
        await session.flush()
        return Executed() if approval_state == "executed" else Failed()

    assert permission == "approval_required"
    expires_at = _now() + timedelta(hours=PENDING_ACTION_EXPIRY_HOURS)
    approval = ApprovalRecord(
        household_id=household_id,
        requested_by_person_id=person.id,
        assistant_id=assistant.id,
        action=f"home_assistant.{domain}.{service}",
        explanation=explanation,
        state="pending",
        payload={"domain": domain, "service": service, "entity_id": entity_id, "data": data or {}},
        expires_at=expires_at,
    )
    session.add(approval)
    session.add(
        ActivityRecord(
            household_id=household_id,
            assistant_id=assistant.id,
            person_id=person.id,
            summary=f"Requested approval for {domain}.{service} on {entity_id}",
            outcome="pending",
            detail={"domain": domain, "service": service, "entity_id": entity_id},
        )
    )
    await session.flush()
    # Best-effort: a single-household deployment has no per-person push target to
    # address, so this is a household-wide persistent notification rather than
    # ADR-002 sec. 5's calendar example's specific-owner notification. Delivery
    # failure is never gating - the pending action still exists and is visible via
    # sensor.kinward_pending_approvals regardless.
    await resolved_ha_client.call_service(
        domain="persistent_notification",
        service="create",
        data={
            "notification_id": f"kinward-approval-{approval.id}",
            "title": "Kinward approval needed",
            "message": f"{person.display_name} requested {domain}.{service} on {entity_id}: {explanation}",
        },
    )
    return PendingApprovalCreated(approval_id=approval.id)


async def list_pending_actions(
    session: AsyncSession, *, household_id: str
) -> list[ApprovalRecord]:
    """Every currently-pending action for this household, oldest first.

    Not admin-gated at this layer - household-shared, non-private data, matching the
    ``GET /pets`` precedent - since this backs a coordinator-polled HA sensor with no
    natural per-user request context. Resolving one (approve/deny) is admin-gated.
    """
    approvals = await session.scalars(
        select(ApprovalRecord)
        .where(ApprovalRecord.household_id == household_id, ApprovalRecord.state == "pending")
        .order_by(ApprovalRecord.created_at)
    )
    return list(approvals)


async def resolve_pending_action(
    session: AsyncSession,
    *,
    household_id: str,
    approval_id: str,
    ha_user_id: str,
    decision: Literal["approve", "deny"],
    settings: Settings | None = None,
    ha_client: HomeAssistantClient | None = None,
) -> ResolveActionOutcome:
    """Approve or deny a pending action (ADR-002 sec. 5). Any current household admin
    may resolve it - there is no per-resource ``affected_person_id`` to require
    instead for the HA device-control case this pass builds (cross-cutting rule 4's
    plural-admin model).
    """
    admin = await resolve_admin(session, ha_user_id=ha_user_id)
    if isinstance(admin, (Unmapped, NotAdmin)):
        return admin

    approval = await session.get(ApprovalRecord, approval_id)
    if approval is None or approval.household_id != household_id:
        return ApprovalNotFound()

    now = _now()
    assert approval.expires_at is not None, "every approval created by request_action has an expiry"
    expires_at = _aware(approval.expires_at)
    ok, error = can_resolve_approval(
        state=approval.state, resolver_is_admin=True, expires_at=expires_at, now=now
    )
    if error is not None:
        if error.code == "expired" and approval.state == "pending":
            approval.state = "expired"
            approval.resolved_at = now
            approval.record_version += 1
            await session.flush()
        return error

    approval.resolved_by_person_id = admin.id
    approval.resolved_at = now

    if decision == "deny":
        approval.state = "denied"
        approval.record_version += 1
        session.add(
            ActivityRecord(
                household_id=household_id,
                assistant_id=approval.assistant_id,
                person_id=admin.id,
                summary=f"Denied pending action: {approval.action}",
                outcome="denied",
                detail={"approval_id": approval.id},
            )
        )
        await session.flush()
        return Denied()

    approval.state = "approved"
    await session.flush()

    ok2, error2 = revalidate_before_execution(
        state=approval.state, expires_at=expires_at, now=_now()
    )
    if error2 is not None:
        if error2.code == "expired":
            approval.state = "expired"
            approval.record_version += 1
            await session.flush()
        return error2

    resolved_ha_client = _resolved_ha_client(settings=settings, ha_client=ha_client)
    payload = approval.payload
    approval_state, activity_outcome, detail = await _submit_and_confirm(
        resolved_ha_client,
        domain=payload["domain"],
        service=payload["service"],
        entity_id=payload["entity_id"],
        data=payload.get("data"),
    )
    approval.state = approval_state
    approval.record_version += 1
    session.add(
        ActivityRecord(
            household_id=household_id,
            assistant_id=approval.assistant_id,
            person_id=admin.id,
            summary=f"Executed approved pending action: {approval.action}",
            outcome=activity_outcome,
            detail={**detail, "approval_id": approval.id},
        )
    )
    await session.flush()
    return Executed() if approval_state == "executed" else Failed()


async def cancel_pending_action(
    session: AsyncSession, *, household_id: str, approval_id: str, ha_user_id: str
) -> CancelActionOutcome:
    """Let the person who requested a pending action withdraw it before anyone

    resolves it (Epic 6 Story 6.1's ``cancelled`` state, defined since migration
    ``010_meaningful_action_approvals`` but unreachable until now). Unlike
    ``resolve_pending_action``, this is gated on being the original requester, not
    admin status - see ``domain.pending_action.can_cancel_approval``.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person

    approval = await session.get(ApprovalRecord, approval_id)
    if approval is None or approval.household_id != household_id:
        return ApprovalNotFound()

    now = _now()
    assert approval.expires_at is not None, "every approval created by request_action has an expiry"
    expires_at = _aware(approval.expires_at)
    ok, error = can_cancel_approval(
        state=approval.state,
        requester_is_owner=person.id == approval.requested_by_person_id,
        expires_at=expires_at,
        now=now,
    )
    if error is not None:
        if error.code == "expired" and approval.state == "pending":
            approval.state = "expired"
            approval.resolved_at = now
            approval.record_version += 1
            await session.flush()
        return error

    approval.state = "cancelled"
    approval.resolved_by_person_id = person.id
    approval.resolved_at = now
    approval.record_version += 1
    session.add(
        ActivityRecord(
            household_id=household_id,
            assistant_id=approval.assistant_id,
            person_id=person.id,
            summary=f"Cancelled pending action: {approval.action}",
            outcome="cancelled",
            detail={"approval_id": approval.id},
        )
    )
    await session.flush()
    return Cancelled()
