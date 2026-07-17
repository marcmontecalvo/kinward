from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.authorization import NotAdmin
from kinward.application.conversation import AccessDenied, AssistantNotFound, Unmapped
from kinward.application.pending_actions import (
    ApprovalNotFound,
    CapabilityDenied,
    Denied,
    Executed,
    Failed,
    InvalidTarget,
    PendingApprovalCreated,
    list_pending_actions,
    request_action,
    resolve_pending_action,
    update_tool_policy,
)
from kinward.domain.pending_action import ApprovalResolutionError
from kinward.integrations.home_assistant import HomeAssistantClient
from kinward.persistence.models import (
    ActivityRecord,
    ApprovalRecord,
    AssistantRecord,
    Base,
    HouseholdRecord,
    PersonRecord,
)


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    owner = PersonRecord(
        household_id=household.id,
        display_name="Marc",
        role="member",
        profile_kind="adult",
        ha_person_id="ha-person-marc",
        ha_user_id="ha-user-marc",
    )
    admin = PersonRecord(
        household_id=household.id,
        display_name="Lisa",
        role="admin",
        profile_kind="adult",
        ha_person_id="ha-person-lisa",
        ha_user_id="ha-user-lisa",
    )
    session.add_all([owner, admin])
    await session.flush()
    assistant = AssistantRecord(
        household_id=household.id, owner_person_id=owner.id, name="Bob", kind="primary"
    )
    session.add(assistant)
    await session.flush()
    return household, owner, admin, assistant


def _ok_ha_client(*, entity_id: str = "light.office") -> HomeAssistantClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"entity_id": entity_id, "state": "off"}])

    return HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )


def _unreachable_ha_client() -> HomeAssistantClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    return HomeAssistantClient(
        base_url="http://ha.invalid", token="fake-token", transport=httpx.MockTransport(handler)
    )


async def test_allowed_capability_executes_immediately() -> None:
    factory = await _factory()
    async with factory() as session:
        _household, owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=_household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="Turning off the office light.",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(result, Executed)

        activity = (await session.scalars(select(ActivityRecord))).one()
        assert activity.outcome == "completed"
        assert activity.detail["entity_id"] == "light.office"


async def test_denied_capability_is_denied_and_never_calls_home_assistant() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)

        def handler(_request: httpx.Request) -> httpx.Response:
            raise AssertionError("control_locks defaults to deny - HA must never be called")

        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="Let the dog walker in.",
            ha_client=HomeAssistantClient(
                base_url="http://ha.invalid",
                token="fake-token",
                transport=httpx.MockTransport(handler),
            ),
        )
        await session.commit()
        assert isinstance(result, CapabilityDenied)
        assert result.capability == "control_locks"

        activity = (await session.scalars(select(ActivityRecord))).one()
        assert activity.outcome == "denied"


async def test_unmapped_domain_service_pair_is_denied() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="climate",
            service="set_temperature",
            entity_id="climate.office",
            data=None,
            explanation="Make it warmer.",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(result, CapabilityDenied)
        assert result.capability is None


async def test_entity_id_domain_mismatch_is_rejected_before_any_permission_check() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="switch.office",
            data=None,
            explanation="Turn off the light.",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(result, InvalidTarget)


async def test_unmapped_caller_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="not-a-synced-user",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        assert isinstance(result, Unmapped)


async def test_caller_without_assistant_access_is_denied() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, admin, assistant = await _seed(session)
        # assistant defaults to owner_only access; admin isn't the owner.
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-lisa",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        assert isinstance(result, AccessDenied)


async def test_unknown_assistant_id_is_not_found() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, _assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id="does-not-exist",
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        assert isinstance(result, AssistantNotFound)


async def test_approval_required_creates_a_pending_action() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner, _admin, assistant = await _seed(session)
        await update_tool_policy(
            session, household_id=household.id, permissions={"control_locks": "approval_required"}
        )

        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="Let the dog walker in.",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(result, PendingApprovalCreated)

        approval = await session.get(ApprovalRecord, result.approval_id)
        assert approval is not None
        assert approval.state == "pending"
        assert approval.requested_by_person_id == owner.id
        assert approval.payload == {
            "domain": "lock",
            "service": "unlock",
            "entity_id": "lock.front_door",
            "data": {},
        }
        assert approval.expires_at is not None

        pending = await list_pending_actions(session, household_id=household.id)
        assert [item.id for item in pending] == [approval.id]


async def test_admin_can_approve_a_pending_action_and_it_executes() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner, admin, assistant = await _seed(session)
        await update_tool_policy(
            session, household_id=household.id, permissions={"control_locks": "approval_required"}
        )
        created = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="Let the dog walker in.",
            ha_client=_ok_ha_client(entity_id="lock.front_door"),
        )
        await session.commit()
        assert isinstance(created, PendingApprovalCreated)

        result = await resolve_pending_action(
            session,
            household_id=household.id,
            approval_id=created.approval_id,
            ha_user_id="ha-user-lisa",
            decision="approve",
            ha_client=_ok_ha_client(entity_id="lock.front_door"),
        )
        await session.commit()
        assert isinstance(result, Executed)

        approval = await session.get(ApprovalRecord, created.approval_id)
        assert approval is not None
        assert approval.state == "executed"
        assert approval.resolved_by_person_id == admin.id
        assert approval.resolved_at is not None

        assert await list_pending_actions(session, household_id=household.id) == []


async def test_admin_can_deny_a_pending_action() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        await update_tool_policy(
            session, household_id=household.id, permissions={"control_locks": "approval_required"}
        )
        created = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(created, PendingApprovalCreated)

        result = await resolve_pending_action(
            session,
            household_id=household.id,
            approval_id=created.approval_id,
            ha_user_id="ha-user-lisa",
            decision="deny",
        )
        await session.commit()
        assert isinstance(result, Denied)
        approval = await session.get(ApprovalRecord, created.approval_id)
        assert approval is not None
        assert approval.state == "denied"


async def test_non_admin_cannot_resolve_a_pending_action() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        await update_tool_policy(
            session, household_id=household.id, permissions={"control_locks": "approval_required"}
        )
        created = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(created, PendingApprovalCreated)

        result = await resolve_pending_action(
            session,
            household_id=household.id,
            approval_id=created.approval_id,
            ha_user_id="ha-user-marc",
            decision="approve",
        )
        assert isinstance(result, NotAdmin)


async def test_resolving_an_unknown_approval_id_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, _assistant = await _seed(session)
        result = await resolve_pending_action(
            session,
            household_id=household.id,
            approval_id="does-not-exist",
            ha_user_id="ha-user-lisa",
            decision="approve",
        )
        assert isinstance(result, ApprovalNotFound)


async def test_expired_approval_transitions_to_expired_on_resolution_attempt() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner, _admin, assistant = await _seed(session)
        await update_tool_policy(
            session, household_id=household.id, permissions={"control_locks": "approval_required"}
        )
        created = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            data=None,
            explanation="x",
            ha_client=_ok_ha_client(),
        )
        await session.commit()
        assert isinstance(created, PendingApprovalCreated)

        approval = await session.get(ApprovalRecord, created.approval_id)
        assert approval is not None
        approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await session.commit()

        result = await resolve_pending_action(
            session,
            household_id=household.id,
            approval_id=created.approval_id,
            ha_user_id="ha-user-lisa",
            decision="approve",
        )
        await session.commit()
        assert isinstance(result, ApprovalResolutionError)
        assert result.code == "expired"

        approval = await session.get(ApprovalRecord, created.approval_id)
        assert approval is not None
        assert approval.state == "expired"


async def test_ha_never_configured_marks_the_action_failed_deterministically() -> None:
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="x",
            ha_client=HomeAssistantClient(base_url=None, token=None),
        )
        await session.commit()
        assert isinstance(result, Failed)

        activity = (await session.scalars(select(ActivityRecord))).one()
        assert activity.outcome == "failed"
        assert activity.detail["reason"] == "not_configured"


async def test_ha_failure_after_send_is_recorded_as_unknown_not_failed() -> None:
    """A timeout/HTTP error *after* HA received the request is genuinely ambiguous -

    HA may have executed it anyway. ``ApprovalRecord``/the returned outcome still
    resolves fail-closed to failed (ADR-002's enum has no "unknown" value), but the
    ``ActivityRecord`` preserves the true ambiguity for audit.
    """
    factory = await _factory()
    async with factory() as session:
        household, _owner, _admin, assistant = await _seed(session)
        result = await request_action(
            session,
            household_id=household.id,
            ha_user_id="ha-user-marc",
            assistant_id=assistant.id,
            domain="light",
            service="turn_off",
            entity_id="light.office",
            data=None,
            explanation="x",
            ha_client=_unreachable_ha_client(),
        )
        await session.commit()
        assert isinstance(result, Failed)

        activity = (await session.scalars(select(ActivityRecord))).one()
        assert activity.outcome == "unknown"
        assert activity.detail["reason"] == "ha_request_failed_after_send"
