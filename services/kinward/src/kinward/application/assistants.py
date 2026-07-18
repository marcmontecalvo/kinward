from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.assistant_policy import get_or_create_assistant_policy
from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.application.visual_packs import DEFAULT_VISUAL_PACK_ID, visual_pack_ids
from kinward.domain.assistant_access import can_address_assistant
from kinward.domain.interview import INTERVIEW_DIMENSIONS
from kinward.persistence.models import AssistantRecord

ACCESS_MODES = frozenset({"owner_only", "household", "allowlist"})


@dataclass(frozen=True)
class AssistantNotFound:
    """No such assistant, or it isn't owned by the resolved person - fail closed either way."""


@dataclass(frozen=True)
class PolicyBlocked:
    code: str
    message: str


@dataclass(frozen=True)
class Deleted:
    assistant_id: str


@dataclass(frozen=True)
class InvalidAccessMode:
    """``access_mode`` wasn't one of the three ADR-002 modes - fail closed."""


@dataclass(frozen=True)
class InvalidVisualPack:
    """``visual_pack_id`` doesn't name a registered catalog entry (Story 3.7) - fail closed."""


async def _count_owned_assistants(session: AsyncSession, *, person_id: str) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(AssistantRecord)
        .where(AssistantRecord.owner_person_id == person_id)
    )
    return int(count or 0)


async def list_own_assistants(
    session: AsyncSession, *, ha_user_id: str
) -> list[AssistantRecord] | Unmapped:
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistants = await session.scalars(
        select(AssistantRecord)
        .where(AssistantRecord.owner_person_id == person.id)
        .order_by(AssistantRecord.created_at)
    )
    return list(assistants)


async def list_household_assistants(
    session: AsyncSession, *, household_id: str
) -> list[AssistantRecord]:
    """Every assistant in the household, unfiltered by ownership or access mode.

    Unlike ``list_own_assistants``/``list_accessible_assistants``, this is never
    privacy-scoped to one resolved person - it exists only for callers that expose
    public identity fields (Story 3.7's name/visual-pack/stage/accent), never
    ``personality``. ``access_mode`` governs who may *address* an assistant, not
    who may see that it exists or what it looks like (``domain/assistant_access.py``).
    """
    assistants = await session.scalars(
        select(AssistantRecord)
        .where(AssistantRecord.household_id == household_id)
        .order_by(AssistantRecord.created_at)
    )
    return list(assistants)


async def list_accessible_assistants(
    session: AsyncSession, *, household_id: str, ha_user_id: str
) -> list[AssistantRecord] | Unmapped:
    """Every assistant the resolved person may address - their own, plus anyone

    else's under ``household``/``allowlist`` mode (ADR-002). A single household
    has no household boundary left to check beyond "did this person resolve at
    all", so this filters in Python rather than needing a JSON-containment query
    that would behave differently on SQLite vs. PostgreSQL.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistants = await session.scalars(
        select(AssistantRecord)
        .where(AssistantRecord.household_id == household_id)
        .order_by(AssistantRecord.created_at)
    )
    return [
        assistant
        for assistant in assistants
        if can_address_assistant(
            owner_person_id=assistant.owner_person_id,
            access_mode=assistant.access_mode,
            allowed_person_ids=assistant.allowed_person_ids,
            caller_person_id=person.id,
        )
    ]


async def create_additional_assistant(
    session: AsyncSession,
    *,
    household_id: str,
    ha_user_id: str,
    name: str,
    personality: dict[str, Any] | None = None,
    visual_pack_id: str | None = None,
    requester_is_admin: bool,
) -> AssistantRecord | Unmapped | PolicyBlocked | InvalidVisualPack:
    """Create another assistant owned by the resolved person, subject to household policy.

    ``requester_is_admin`` reflects the caller's own admin status (resolved by the API
    layer, same as every other admin-gated mutation) - the approval gate, when on,
    restricts *who may create*, not *who it's created for*: only an admin can create
    any additional assistant while the gate is active, matching how HA itself
    restricts new-user creation to admins. There is no product-enforced ceiling by
    default (``max_assistants_per_person`` is ``None``) - a household may cap it.

    Like every newly-synced person's primary assistant (``people_sync.sync_people``),
    a fresh additional assistant starts at ``interview_state="not_started"`` (Story
    3.5) - onboarding isn't limited to a person's very first assistant.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person

    if visual_pack_id is not None and visual_pack_id not in visual_pack_ids():
        return InvalidVisualPack()

    policy = await get_or_create_assistant_policy(session, household_id=household_id)
    if policy.require_admin_approval_for_creation and not requester_is_admin:
        return PolicyBlocked(
            code="admin_approval_required",
            message=(
                "An administrator must create additional assistants while this "
                "household requires approval."
            ),
        )

    existing_count = await _count_owned_assistants(session, person_id=person.id)
    if (
        policy.max_assistants_per_person is not None
        and existing_count >= policy.max_assistants_per_person
    ):
        return PolicyBlocked(
            code="max_assistants_reached",
            message=(
                f"This person already has the maximum of "
                f"{policy.max_assistants_per_person} assistants."
            ),
        )

    assistant = AssistantRecord(
        household_id=household_id,
        owner_person_id=person.id,
        name=name.strip(),
        kind="primary",
        personality=personality or {},
        visual_pack_id=visual_pack_id or DEFAULT_VISUAL_PACK_ID,
        interview_state="not_started",
    )
    session.add(assistant)
    await session.flush()
    return assistant


async def delete_own_assistant(
    session: AsyncSession, *, ha_user_id: str, assistant_id: str
) -> Deleted | AssistantNotFound | Unmapped | PolicyBlocked:
    """Delete one of the resolved person's own assistants - never their last one.

    Kinward always gives a synced person at least one assistant (auto-created on
    sync); letting someone delete their last one would leave conversation.kinward
    with nothing to resolve to for them - the same class of problem
    domain/admin_invariant.py protects against for "last admin".
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistant = await session.get(AssistantRecord, assistant_id)
    if assistant is None or assistant.owner_person_id != person.id:
        return AssistantNotFound()

    existing_count = await _count_owned_assistants(session, person_id=person.id)
    if existing_count <= 1:
        return PolicyBlocked(
            code="last_assistant", message="Cannot delete a person's only remaining assistant."
        )

    await session.delete(assistant)
    await session.flush()
    return Deleted(assistant_id=assistant_id)


async def update_own_assistant(
    session: AsyncSession,
    *,
    ha_user_id: str,
    assistant_id: str,
    name: str | None = None,
    personality: dict[str, Any] | None = None,
    access_mode: str | None = None,
    allowed_person_ids: list[str] | None = None,
    visual_pack_id: str | None = None,
) -> AssistantRecord | AssistantNotFound | Unmapped | InvalidAccessMode | InvalidVisualPack:
    """Let an owner rename, set personality/interaction preferences, change the

    ADR-002 access mode, or swap the visual-identity pack (Story 3.7) on one of
    their own assistants.

    Preferences and access mode never alter authority, privacy, or action policy:
    this only ever touches the assistant's own fields, never anything on the
    owning ``PersonRecord``, and never another person's assistant. Access mode
    controls who may *address* this assistant at all - it never affects which
    conversational-memory peer is used, and it grants no tool permission.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistant = await session.get(AssistantRecord, assistant_id)
    if assistant is None or assistant.owner_person_id != person.id:
        return AssistantNotFound()
    if access_mode is not None and access_mode not in ACCESS_MODES:
        return InvalidAccessMode()
    if visual_pack_id is not None and visual_pack_id not in visual_pack_ids():
        return InvalidVisualPack()
    if name is not None:
        assistant.name = name.strip()
    if personality is not None:
        assistant.personality = personality
    if access_mode is not None:
        assistant.access_mode = access_mode
    if allowed_person_ids is not None:
        assistant.allowed_person_ids = allowed_person_ids
    if visual_pack_id is not None:
        assistant.visual_pack_id = visual_pack_id
    assistant.record_version += 1
    await session.flush()
    return assistant


async def restart_interview(
    session: AsyncSession, *, ha_user_id: str, assistant_id: str
) -> AssistantRecord | AssistantNotFound | Unmapped:
    """Let an owner explicitly redo their assistant's personality interview (Story 3.5).

    Clears every interview-dimension key from ``personality`` (a manually-set,
    non-interview key is left untouched) and resets state to ``not_started``, so
    the next conversation turn with this assistant opens with the interview again.
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistant = await session.get(AssistantRecord, assistant_id)
    if assistant is None or assistant.owner_person_id != person.id:
        return AssistantNotFound()
    dimension_names = {question.dimension for question in INTERVIEW_DIMENSIONS}
    assistant.personality = {
        key: value for key, value in assistant.personality.items() if key not in dimension_names
    }
    assistant.interview_state = "not_started"
    assistant.record_version += 1
    await session.flush()
    return assistant
