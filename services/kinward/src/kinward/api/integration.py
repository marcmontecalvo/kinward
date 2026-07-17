from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.assistant_policy import (
    get_or_create_assistant_policy,
    update_assistant_policy,
)
from kinward.application.assistants import AssistantNotFound
from kinward.application.assistants import Deleted as AssistantDeleted
from kinward.application.assistants import (
    InvalidAccessMode,
    PolicyBlocked,
    create_additional_assistant,
    delete_own_assistant,
    list_accessible_assistants,
    list_own_assistants,
    update_own_assistant,
)
from kinward.application.authorization import NotAdmin, resolve_admin
from kinward.application.conversation import AccessDenied
from kinward.application.conversation import AssistantNotFound as AddressedAssistantNotFound
from kinward.application.conversation import (
    AlreadyTerminal,
    Completed,
    Deleted,
    TopicNotFound,
    TurnNotFound,
    Unmapped,
    cancel_turn,
    delete_topic,
    get_topic,
    handle_conversation_request,
    list_topics,
    update_topic,
)
from kinward.application.knowledge import Disposed as KnowledgeDisposed
from kinward.application.knowledge import (
    FactNotFound,
    NotConfirmed,
    NotPending,
    ProviderUnavailable,
    confirm_observation,
    correct_fact,
    delete_fact,
    list_confirmed_facts,
    list_pending_observations,
    reject_observation,
)
from kinward.application.pending_actions import (
    ApprovalNotFound,
    CapabilityDenied,
    Denied,
    Executed,
    Failed,
    InvalidTarget,
    PendingApprovalCreated,
    get_or_create_tool_policy,
    list_pending_actions,
    request_action,
    resolve_pending_action,
    update_tool_policy,
)
from kinward.application.people import PersonNotFound, list_people, reclassify_person
from kinward.application.person_deletion import AdminInvariantBlocked
from kinward.application.person_deletion import Deleted as PersonDeleted
from kinward.application.person_deletion import delete_person
from kinward.application.pets import PetNotFound
from kinward.application.pets import Deleted as PetDeleted
from kinward.application.pets import create_pet, delete_pet, list_pets, update_pet
from kinward.application.provider_settings import (
    get_or_create_provider_settings,
    update_provider_settings,
)
from kinward.config import Settings
from kinward.domain.pending_action import ApprovalResolutionError
from kinward.memory.contracts import KnowledgeStoreProvider
from kinward.memory.factory import knowledge_store_provider
from kinward.persistence.models import (
    ApprovalRecord,
    AssistantPolicyRecord,
    AssistantRecord,
    HomeAssistantToolPolicyRecord,
    KnowledgeFactRecord,
    PersonRecord,
    ProviderSettingsRecord,
    TopicRecord,
    TopicTurnRecord,
)
from kinward.application.household_summary import fetch_household_summary
from kinward.application.people_sync import SyncedPerson, sync_people
from kinward.health import CapabilityState
from kinward.persistence.models import IntegrationTokenRecord
from kinward.persistence.session import session_dependency
from kinward.api.security import require_integration_token

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

IntegrationToken = Annotated[IntegrationTokenRecord, Depends(require_integration_token)]
Session = Annotated[AsyncSession, Depends(session_dependency)]


def _settings_dependency(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


AppSettings = Annotated[Settings, Depends(_settings_dependency)]


class IntegrationContextResponse(BaseModel):
    household_id: str = Field(serialization_alias="householdId")
    household_name: str = Field(serialization_alias="householdName")
    contract_version: str = Field(default="v1", serialization_alias="contractVersion")


class HouseholdSummaryPayload(BaseModel):
    adult_count: int = Field(serialization_alias="adultCount")
    child_count: int = Field(serialization_alias="childCount")


class NotYetImplementedCapability(BaseModel):
    state: CapabilityState = "intentionally-disabled"
    reason: str = "not-yet-implemented"


class BriefingCapability(NotYetImplementedCapability):
    summary: str | None = None


class AttentionCapability(NotYetImplementedCapability):
    count: int | None = None


class NextEventCapability(NotYetImplementedCapability):
    summary: str | None = None
    starts_at: str | None = Field(default=None, serialization_alias="startsAt")


class IntegrationSummaryResponse(BaseModel):
    contract_version: str = Field(default="v1", serialization_alias="contractVersion")
    household: HouseholdSummaryPayload
    briefing: BriefingCapability = BriefingCapability()
    attention: AttentionCapability = AttentionCapability()
    next_event: NextEventCapability = Field(
        default_factory=NextEventCapability, serialization_alias="nextEvent"
    )


def _household_not_configured() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "household_not_configured", "message": "No household has been set up yet."},
    )


def _admin_required() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "admin_required",
            "message": "Household administrator authorization is required for this operation.",
        },
    )


async def _require_admin(session: AsyncSession, *, ha_user_id: str) -> PersonRecord:
    result = await resolve_admin(session, ha_user_id=ha_user_id)
    if isinstance(result, (Unmapped, NotAdmin)):
        raise _admin_required()
    return result


@router.get("/context", response_model=IntegrationContextResponse)
async def integration_context(
    _token: IntegrationToken, session: Session
) -> IntegrationContextResponse:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    return IntegrationContextResponse(household_id=summary.id, household_name=summary.name)


@router.get("/summary", response_model=IntegrationSummaryResponse)
async def integration_summary(
    _token: IntegrationToken, session: Session
) -> IntegrationSummaryResponse:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    return IntegrationSummaryResponse(
        household=HouseholdSummaryPayload(
            adult_count=summary.adult_count, child_count=summary.child_count
        )
    )


class PersonPayload(BaseModel):
    id: str
    display_name: str = Field(serialization_alias="displayName")


@router.get("/people", response_model=list[PersonPayload])
async def integration_people(_token: IntegrationToken, session: Session) -> list[PersonPayload]:
    people = await list_people(session)
    return [PersonPayload(id=person.id, display_name=person.display_name) for person in people]


class PersonSyncItem(BaseModel):
    ha_person_id: str = Field(alias="haPersonId", min_length=1, max_length=64)
    ha_user_id: str | None = Field(default=None, alias="haUserId", min_length=1, max_length=64)
    display_name: str = Field(alias="displayName", min_length=1, max_length=120)
    is_admin: bool = Field(default=False, alias="isAdmin")


class SyncedPersonPayload(BaseModel):
    id: str
    ha_person_id: str = Field(serialization_alias="haPersonId")
    ha_user_id: str | None = Field(serialization_alias="haUserId")
    display_name: str = Field(serialization_alias="displayName")
    role: str

    @classmethod
    def from_record(cls, person: PersonRecord) -> SyncedPersonPayload:
        assert person.ha_person_id is not None, "sync always sets ha_person_id"
        return cls(
            id=person.id,
            ha_person_id=person.ha_person_id,
            ha_user_id=person.ha_user_id,
            display_name=person.display_name,
            role=person.role,
        )


@router.put("/people/sync", response_model=list[SyncedPersonPayload])
async def integration_sync_people(
    body: list[PersonSyncItem],
    _token: IntegrationToken,
    session: Session,
) -> list[SyncedPersonPayload]:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    synced = await sync_people(
        session,
        household_id=summary.id,
        people=[
            SyncedPerson(
                ha_person_id=item.ha_person_id,
                ha_user_id=item.ha_user_id,
                display_name=item.display_name,
                is_admin=item.is_admin,
            )
            for item in body
        ],
    )
    await session.commit()
    return [SyncedPersonPayload.from_record(person) for person in synced]


AdminHaUserIdQuery = Annotated[str, Query(alias="haUserId", min_length=1, max_length=64)]


class PersonProfilePayload(BaseModel):
    id: str
    display_name: str = Field(serialization_alias="displayName")
    role: str
    profile_kind: str = Field(serialization_alias="profileKind")
    classification: str

    @classmethod
    def from_record(cls, person: PersonRecord) -> PersonProfilePayload:
        return cls(
            id=person.id,
            display_name=person.display_name,
            role=person.role,
            profile_kind=person.profile_kind,
            classification=person.classification,
        )


class ReclassifyPersonRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    profile_kind: Literal["adult", "teen", "child"] = Field(alias="profileKind")


def _person_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "person_not_found"})


@router.patch("/people/{person_id}/reclassify", response_model=PersonProfilePayload)
async def integration_reclassify_person(
    person_id: str, body: ReclassifyPersonRequest, _token: IntegrationToken, session: Session
) -> PersonProfilePayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    await _require_admin(session, ha_user_id=body.ha_user_id)
    result = await reclassify_person(
        session, household_id=summary.id, person_id=person_id, profile_kind=body.profile_kind
    )
    if isinstance(result, PersonNotFound):
        await session.rollback()
        raise _person_not_found()
    await session.commit()
    return PersonProfilePayload.from_record(result)


def _admin_invariant_blocked(violation: AdminInvariantBlocked) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": violation.code, "message": violation.message},
    )


@router.delete("/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def integration_delete_person(
    person_id: str, ha_user_id: AdminHaUserIdQuery, _token: IntegrationToken, session: Session
) -> None:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    await _require_admin(session, ha_user_id=ha_user_id)
    result = await delete_person(session, household_id=summary.id, person_id=person_id)
    if isinstance(result, PersonNotFound):
        await session.rollback()
        raise _person_not_found()
    if isinstance(result, AdminInvariantBlocked):
        await session.rollback()
        raise _admin_invariant_blocked(result)
    assert isinstance(result, PersonDeleted)
    await session.commit()


class PetPayload(BaseModel):
    id: str
    display_name: str = Field(serialization_alias="displayName")
    species: str
    shared_facts: list[str] = Field(serialization_alias="sharedFacts")

    @classmethod
    def from_record(cls, pet: Any) -> PetPayload:
        return cls(
            id=pet.id,
            display_name=pet.display_name,
            species=pet.species,
            shared_facts=list(pet.shared_facts),
        )


class CreatePetRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    display_name: str = Field(alias="displayName", min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=80)
    shared_facts: list[str] = Field(default_factory=list, alias="sharedFacts")


class UpdatePetRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    display_name: str | None = Field(default=None, alias="displayName", max_length=120)
    species: str | None = Field(default=None, max_length=80)
    shared_facts: list[str] | None = Field(default=None, alias="sharedFacts")


def _pet_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "pet_not_found"})


@router.get("/pets", response_model=list[PetPayload])
async def integration_list_pets(_token: IntegrationToken, session: Session) -> list[PetPayload]:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    pets = await list_pets(session, household_id=summary.id)
    return [PetPayload.from_record(pet) for pet in pets]


@router.post("/pets", response_model=PetPayload, status_code=status.HTTP_201_CREATED)
async def integration_create_pet(
    body: CreatePetRequest, _token: IntegrationToken, session: Session
) -> PetPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    await _require_admin(session, ha_user_id=body.ha_user_id)
    pet = await create_pet(
        session,
        household_id=summary.id,
        display_name=body.display_name,
        species=body.species,
        shared_facts=body.shared_facts,
    )
    await session.commit()
    return PetPayload.from_record(pet)


@router.patch("/pets/{pet_id}", response_model=PetPayload)
async def integration_update_pet(
    pet_id: str, body: UpdatePetRequest, _token: IntegrationToken, session: Session
) -> PetPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    await _require_admin(session, ha_user_id=body.ha_user_id)
    result = await update_pet(
        session,
        household_id=summary.id,
        pet_id=pet_id,
        display_name=body.display_name,
        species=body.species,
        shared_facts=body.shared_facts,
    )
    if isinstance(result, PetNotFound):
        await session.rollback()
        raise _pet_not_found()
    await session.commit()
    return PetPayload.from_record(result)


@router.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def integration_delete_pet(
    pet_id: str, ha_user_id: AdminHaUserIdQuery, _token: IntegrationToken, session: Session
) -> None:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    await _require_admin(session, ha_user_id=ha_user_id)
    result = await delete_pet(session, household_id=summary.id, pet_id=pet_id)
    if isinstance(result, PetNotFound):
        await session.rollback()
        raise _pet_not_found()
    assert isinstance(result, PetDeleted)
    await session.commit()


class AssistantPayload(BaseModel):
    id: str
    name: str
    personality: dict[str, Any]
    access_mode: str = Field(serialization_alias="accessMode")
    allowed_person_ids: list[str] = Field(serialization_alias="allowedPersonIds")

    @classmethod
    def from_record(cls, assistant: AssistantRecord) -> AssistantPayload:
        return cls(
            id=assistant.id,
            name=assistant.name,
            personality=dict(assistant.personality),
            access_mode=assistant.access_mode,
            allowed_person_ids=list(assistant.allowed_person_ids),
        )


class CreateAssistantRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    personality: dict[str, Any] | None = None


class UpdateOwnAssistantRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=120)
    personality: dict[str, Any] | None = None
    access_mode: str | None = Field(default=None, alias="accessMode")
    allowed_person_ids: list[str] | None = Field(default=None, alias="allowedPersonIds")


def _assistant_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "assistant_not_found"})


def _invalid_access_mode() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_access_mode", "message": "accessMode must be one of: owner_only, household, allowlist."},
    )


def _policy_blocked(violation: PolicyBlocked) -> HTTPException:
    status_code = (
        status.HTTP_403_FORBIDDEN
        if violation.code == "admin_approval_required"
        else status.HTTP_409_CONFLICT
    )
    return HTTPException(
        status_code=status_code, detail={"code": violation.code, "message": violation.message}
    )


async def _is_admin(session: AsyncSession, *, ha_user_id: str) -> bool:
    result = await resolve_admin(session, ha_user_id=ha_user_id)
    return not isinstance(result, (Unmapped, NotAdmin))


@router.get("/assistants", response_model=list[AssistantPayload])
async def integration_list_own_assistants(
    ha_user_id: AdminHaUserIdQuery, _token: IntegrationToken, session: Session
) -> list[AssistantPayload]:
    result = await list_own_assistants(session, ha_user_id=ha_user_id)
    if isinstance(result, Unmapped):
        return []
    return [AssistantPayload.from_record(assistant) for assistant in result]


@router.get("/assistants/accessible", response_model=list[AssistantPayload])
async def integration_list_accessible_assistants(
    ha_user_id: AdminHaUserIdQuery, _token: IntegrationToken, session: Session
) -> list[AssistantPayload]:
    """Every assistant this person may address (ADR-002) - their own, plus anyone
    else's under household/allowlist mode. Superset of ``GET /assistants``.
    """
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    result = await list_accessible_assistants(session, household_id=summary.id, ha_user_id=ha_user_id)
    if isinstance(result, Unmapped):
        return []
    return [AssistantPayload.from_record(assistant) for assistant in result]


@router.post("/assistants", response_model=AssistantPayload, status_code=status.HTTP_201_CREATED)
async def integration_create_assistant(
    body: CreateAssistantRequest, _token: IntegrationToken, session: Session
) -> AssistantPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    requester_is_admin = await _is_admin(session, ha_user_id=body.ha_user_id)
    result = await create_additional_assistant(
        session,
        household_id=summary.id,
        ha_user_id=body.ha_user_id,
        name=body.name,
        personality=body.personality,
        requester_is_admin=requester_is_admin,
    )
    if isinstance(result, Unmapped):
        await session.rollback()
        raise _assistant_not_found()
    if isinstance(result, PolicyBlocked):
        await session.rollback()
        raise _policy_blocked(result)
    await session.commit()
    return AssistantPayload.from_record(result)


@router.patch("/assistants/{assistant_id}", response_model=AssistantPayload)
async def integration_update_own_assistant(
    assistant_id: str, body: UpdateOwnAssistantRequest, _token: IntegrationToken, session: Session
) -> AssistantPayload:
    result = await update_own_assistant(
        session,
        ha_user_id=body.ha_user_id,
        assistant_id=assistant_id,
        name=body.name,
        personality=body.personality,
        access_mode=body.access_mode,
        allowed_person_ids=body.allowed_person_ids,
    )
    if isinstance(result, (Unmapped, AssistantNotFound)):
        await session.rollback()
        raise _assistant_not_found()
    if isinstance(result, InvalidAccessMode):
        await session.rollback()
        raise _invalid_access_mode()
    await session.commit()
    return AssistantPayload.from_record(result)


@router.delete("/assistants/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def integration_delete_own_assistant(
    assistant_id: str, ha_user_id: AdminHaUserIdQuery, _token: IntegrationToken, session: Session
) -> None:
    result = await delete_own_assistant(session, ha_user_id=ha_user_id, assistant_id=assistant_id)
    if isinstance(result, (Unmapped, AssistantNotFound)):
        await session.rollback()
        raise _assistant_not_found()
    if isinstance(result, PolicyBlocked):
        await session.rollback()
        raise _policy_blocked(result)
    assert isinstance(result, AssistantDeleted)
    await session.commit()


class AssistantPolicyPayload(BaseModel):
    max_assistants_per_person: int | None = Field(serialization_alias="maxAssistantsPerPerson")
    require_admin_approval_for_creation: bool = Field(
        serialization_alias="requireAdminApprovalForCreation"
    )

    @classmethod
    def from_record(cls, policy: AssistantPolicyRecord) -> AssistantPolicyPayload:
        return cls(
            max_assistants_per_person=policy.max_assistants_per_person,
            require_admin_approval_for_creation=policy.require_admin_approval_for_creation,
        )


class UpdateAssistantPolicyRequest(BaseModel):
    """Both fields are required: the options flow always submits the whole form,
    prefilled from a prior GET, so there's no partial-update ambiguity to preserve
    here the way there is for provider_settings' write-only API key field.
    """

    max_assistants_per_person: int | None = Field(alias="maxAssistantsPerPerson")
    require_admin_approval_for_creation: bool = Field(alias="requireAdminApprovalForCreation")


@router.get("/settings/assistant-policy", response_model=AssistantPolicyPayload)
async def integration_get_assistant_policy(
    _token: IntegrationToken, session: Session
) -> AssistantPolicyPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    policy = await get_or_create_assistant_policy(session, household_id=summary.id)
    await session.commit()
    return AssistantPolicyPayload.from_record(policy)


@router.patch("/settings/assistant-policy", response_model=AssistantPolicyPayload)
async def integration_update_assistant_policy(
    body: UpdateAssistantPolicyRequest, _token: IntegrationToken, session: Session
) -> AssistantPolicyPayload:
    """Gated by the integration bearer token alone, like ``/settings/providers`` -
    only the Kinward HA integration's own options flow calls this, and HA already
    restricts that to admins.
    """
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    policy = await update_assistant_policy(
        session,
        household_id=summary.id,
        max_assistants_per_person=body.max_assistants_per_person,
        require_admin_approval_for_creation=body.require_admin_approval_for_creation,
    )
    await session.commit()
    return AssistantPolicyPayload.from_record(policy)


class ConversationRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, alias="conversationId", max_length=36)
    language: str = Field(default="en", min_length=2, max_length=16)
    assistant_id: str | None = Field(default=None, alias="assistantId", max_length=36)
    device_id: str | None = Field(default=None, alias="deviceId", max_length=255)


class ConversationResponse(BaseModel):
    conversation_id: str | None = Field(serialization_alias="conversationId")
    outcome: str
    response_text: str = Field(serialization_alias="responseText")
    mapped: bool


UNMAPPED_RESPONSE_TEXT = "This Home Assistant user isn't linked to a Kinward profile yet."


@router.post("/conversation", response_model=ConversationResponse)
async def integration_conversation(
    body: ConversationRequest, _token: IntegrationToken, session: Session, settings: AppSettings
) -> ConversationResponse:
    result = await handle_conversation_request(
        session,
        ha_user_id=body.ha_user_id,
        text=body.text,
        conversation_id=body.conversation_id,
        language=body.language,
        assistant_id=body.assistant_id,
        device_id=body.device_id,
        settings=settings,
    )
    await session.commit()
    if isinstance(result, Unmapped):
        return ConversationResponse(
            conversation_id=None,
            outcome="unmapped",
            response_text=UNMAPPED_RESPONSE_TEXT,
            mapped=False,
        )
    if isinstance(result, AddressedAssistantNotFound):
        return ConversationResponse(
            conversation_id=None,
            outcome="assistant_not_found",
            response_text="That assistant doesn't exist.",
            mapped=True,
        )
    if isinstance(result, AccessDenied):
        return ConversationResponse(
            conversation_id=None,
            outcome="access_denied",
            response_text=f"You don't have access to {result.assistant_name}.",
            mapped=True,
        )
    assert isinstance(result, Completed)
    return ConversationResponse(
        conversation_id=result.conversation_id,
        outcome="completed",
        response_text=result.response_text,
        mapped=True,
    )


class CancelTurnRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)


class CancelTurnResponse(BaseModel):
    turn_id: str = Field(serialization_alias="turnId")
    outcome: str
    already_terminal: bool = Field(serialization_alias="alreadyTerminal")


def _turn_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "turn_not_found"})


@router.post("/conversation/turns/{turn_id}/cancel", response_model=CancelTurnResponse)
async def cancel_conversation_turn(
    turn_id: str, body: CancelTurnRequest, _token: IntegrationToken, session: Session
) -> CancelTurnResponse:
    result = await cancel_turn(session, turn_id=turn_id, ha_user_id=body.ha_user_id)
    if isinstance(result, (Unmapped, TurnNotFound)):
        raise _turn_not_found()
    assert isinstance(result, AlreadyTerminal)
    return CancelTurnResponse(
        turn_id=result.turn_id, outcome=result.outcome, already_terminal=True
    )


HaUserIdQuery = Annotated[str, Query(alias="haUserId", min_length=1, max_length=64)]


class TopicPayload(BaseModel):
    id: str
    title: str | None
    state: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_record(cls, topic: TopicRecord) -> TopicPayload:
        return cls(
            id=topic.id,
            title=topic.title,
            state=topic.state,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
        )


class TopicTurnPayload(BaseModel):
    request_text: str = Field(serialization_alias="requestText")
    response_text: str = Field(serialization_alias="responseText")
    outcome: str
    created_at: datetime = Field(serialization_alias="createdAt")


class TopicDetailPayload(TopicPayload):
    turns: list[TopicTurnPayload]


class UpdateTopicRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    title: str | None = Field(default=None, max_length=200)
    state: Literal["open", "archived"] | None = None


def _topic_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "topic_not_found"})


@router.get("/topics", response_model=list[TopicPayload])
async def integration_list_topics(
    ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> list[TopicPayload]:
    result = await list_topics(session, ha_user_id=ha_user_id)
    if isinstance(result, Unmapped):
        raise _topic_not_found()
    return [TopicPayload.from_record(topic) for topic in result]


@router.get("/topics/{topic_id}", response_model=TopicDetailPayload)
async def integration_get_topic(
    topic_id: str, ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> TopicDetailPayload:
    result = await get_topic(session, ha_user_id=ha_user_id, topic_id=topic_id)
    if isinstance(result, (Unmapped, TopicNotFound)):
        raise _topic_not_found()
    turns = await session.scalars(
        select(TopicTurnRecord)
        .where(TopicTurnRecord.topic_id == topic_id)
        .order_by(TopicTurnRecord.created_at)
    )
    return TopicDetailPayload(
        **TopicPayload.from_record(result).model_dump(),
        turns=[
            TopicTurnPayload(
                request_text=turn.request_text,
                response_text=turn.response_text,
                outcome=turn.outcome,
                created_at=turn.created_at,
            )
            for turn in turns
        ],
    )


@router.patch("/topics/{topic_id}", response_model=TopicPayload)
async def integration_update_topic(
    topic_id: str, body: UpdateTopicRequest, _token: IntegrationToken, session: Session
) -> TopicPayload:
    result = await update_topic(
        session,
        ha_user_id=body.ha_user_id,
        topic_id=topic_id,
        title=body.title,
        state=body.state,
    )
    if isinstance(result, (Unmapped, TopicNotFound)):
        await session.rollback()
        raise _topic_not_found()
    await session.commit()
    return TopicPayload.from_record(result)


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def integration_delete_topic(
    topic_id: str, ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> None:
    result = await delete_topic(session, ha_user_id=ha_user_id, topic_id=topic_id)
    if isinstance(result, (Unmapped, TopicNotFound)):
        await session.rollback()
        raise _topic_not_found()
    assert isinstance(result, Deleted)
    await session.commit()


class ProviderSettingsPayload(BaseModel):
    model_provider: str = Field(serialization_alias="modelProvider")
    model_base_url: str | None = Field(serialization_alias="modelBaseUrl")
    model_name: str | None = Field(serialization_alias="modelName")
    has_model_api_key: bool = Field(serialization_alias="hasModelApiKey")
    memory_backend: str = Field(serialization_alias="memoryBackend")
    honcho_url: str | None = Field(serialization_alias="honchoUrl")
    knowledge_backend: str = Field(serialization_alias="knowledgeBackend")
    llm_wiki_url: str | None = Field(serialization_alias="llmWikiUrl")

    @classmethod
    def from_record(cls, settings: ProviderSettingsRecord) -> ProviderSettingsPayload:
        return cls(
            model_provider=settings.model_provider,
            model_base_url=settings.model_base_url,
            model_name=settings.model_name,
            has_model_api_key=bool(settings.model_api_key),
            memory_backend=settings.memory_backend,
            honcho_url=settings.honcho_url,
            knowledge_backend=settings.knowledge_backend,
            llm_wiki_url=settings.llm_wiki_url,
        )


class UpdateProviderSettingsRequest(BaseModel):
    model_provider: Literal["none", "openai", "openai-compatible", "anthropic"] | None = Field(
        default=None, alias="modelProvider"
    )
    model_base_url: str | None = Field(default=None, alias="modelBaseUrl")
    model_name: str | None = Field(default=None, alias="modelName")
    model_api_key: str | None = Field(default=None, alias="modelApiKey")
    memory_backend: Literal["none", "honcho"] | None = Field(default=None, alias="memoryBackend")
    honcho_url: str | None = Field(default=None, alias="honchoUrl")
    knowledge_backend: Literal["none", "llm_wiki"] | None = Field(default=None, alias="knowledgeBackend")
    llm_wiki_url: str | None = Field(default=None, alias="llmWikiUrl")


@router.get("/settings/providers", response_model=ProviderSettingsPayload)
async def integration_get_provider_settings(
    _token: IntegrationToken, session: Session
) -> ProviderSettingsPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    settings = await get_or_create_provider_settings(session, household_id=summary.id)
    await session.commit()
    return ProviderSettingsPayload.from_record(settings)


@router.patch("/settings/providers", response_model=ProviderSettingsPayload)
async def integration_update_provider_settings(
    body: UpdateProviderSettingsRequest, _token: IntegrationToken, session: Session
) -> ProviderSettingsPayload:
    """Gated by the integration bearer token alone, like ``/people/sync`` - only the Kinward
    HA integration's own options flow calls this, and HA already restricts that to admins.
    """
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    settings = await update_provider_settings(
        session,
        household_id=summary.id,
        model_provider=body.model_provider,
        model_base_url=body.model_base_url,
        model_name=body.model_name,
        model_api_key=body.model_api_key,
        memory_backend=body.memory_backend,
        honcho_url=body.honcho_url,
        knowledge_backend=body.knowledge_backend,
        llm_wiki_url=body.llm_wiki_url,
    )
    await session.commit()
    return ProviderSettingsPayload.from_record(settings)


class KnowledgeFactPayload(BaseModel):
    id: str
    subject: str
    predicate: str
    value: Any
    privacy: str
    knowledge_state: str = Field(serialization_alias="knowledgeState")
    deletion_status: str = Field(serialization_alias="deletionStatus")
    confidence: float
    source_system: str = Field(serialization_alias="sourceSystem")
    created_at: datetime = Field(serialization_alias="createdAt")
    expires_at: datetime | None = Field(serialization_alias="expiresAt")
    confirmed_at: datetime | None = Field(serialization_alias="confirmedAt")

    @classmethod
    def from_record(cls, record: KnowledgeFactRecord) -> KnowledgeFactPayload:
        return cls(
            id=record.id,
            subject=record.subject,
            predicate=record.predicate,
            value=record.value,
            privacy=record.privacy,
            knowledge_state=record.knowledge_state,
            deletion_status=record.deletion_status,
            confidence=record.confidence,
            source_system=record.source_system,
            created_at=record.created_at,
            expires_at=record.expires_at,
            confirmed_at=record.confirmed_at,
        )


class HaUserIdBody(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)


class CorrectFactRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    value: Any
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


def _fact_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "knowledge_fact_not_found"})


def _fact_not_pending() -> HTTPException:
    return HTTPException(status_code=409, detail={"code": "knowledge_fact_not_pending"})


def _fact_not_confirmed() -> HTTPException:
    return HTTPException(status_code=409, detail={"code": "knowledge_fact_not_confirmed"})


def _provider_unavailable() -> HTTPException:
    return HTTPException(status_code=409, detail={"code": "knowledge_provider_unavailable"})


async def _knowledge_provider(session: AsyncSession, *, household_id: str) -> KnowledgeStoreProvider:
    provider_settings = await get_or_create_provider_settings(session, household_id=household_id)
    return knowledge_store_provider(
        backend=provider_settings.knowledge_backend, url=provider_settings.llm_wiki_url
    )


@router.get("/knowledge/observations", response_model=list[KnowledgeFactPayload])
async def integration_list_pending_observations(
    ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> list[KnowledgeFactPayload]:
    """A person's own pending inferred observations only (AD-25) - fails closed to an

    empty list for an unmapped caller rather than a distinct error, same as every
    other own-data listing endpoint.
    """
    result = await list_pending_observations(session, ha_user_id=ha_user_id)
    if isinstance(result, Unmapped):
        return []
    return [KnowledgeFactPayload.from_record(record) for record in result]


@router.post("/knowledge/observations/{fact_id}/confirm", response_model=KnowledgeFactPayload)
async def integration_confirm_observation(
    fact_id: str, body: HaUserIdBody, _token: IntegrationToken, session: Session
) -> KnowledgeFactPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    provider = await _knowledge_provider(session, household_id=summary.id)
    result = await confirm_observation(session, provider, ha_user_id=body.ha_user_id, fact_id=fact_id)
    if isinstance(result, (Unmapped, FactNotFound)):
        await session.rollback()
        raise _fact_not_found()
    if isinstance(result, NotPending):
        await session.rollback()
        raise _fact_not_pending()
    if isinstance(result, ProviderUnavailable):
        await session.rollback()
        raise _provider_unavailable()
    await session.commit()
    return KnowledgeFactPayload.from_record(result)


@router.post("/knowledge/observations/{fact_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def integration_reject_observation(
    fact_id: str, body: HaUserIdBody, _token: IntegrationToken, session: Session
) -> None:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    provider = await _knowledge_provider(session, household_id=summary.id)
    result = await reject_observation(session, provider, ha_user_id=body.ha_user_id, fact_id=fact_id)
    if isinstance(result, (Unmapped, FactNotFound)):
        await session.rollback()
        raise _fact_not_found()
    if isinstance(result, NotPending):
        await session.rollback()
        raise _fact_not_pending()
    assert isinstance(result, KnowledgeDisposed)
    await session.commit()


@router.get("/knowledge/facts", response_model=list[KnowledgeFactPayload])
async def integration_list_confirmed_facts(
    ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> list[KnowledgeFactPayload]:
    """A person's own confirmed durable facts only - inspection per Story 4.4."""
    result = await list_confirmed_facts(session, ha_user_id=ha_user_id)
    if isinstance(result, Unmapped):
        return []
    return [KnowledgeFactPayload.from_record(record) for record in result]


@router.patch("/knowledge/facts/{fact_id}", response_model=KnowledgeFactPayload)
async def integration_correct_fact(
    fact_id: str, body: CorrectFactRequest, _token: IntegrationToken, session: Session
) -> KnowledgeFactPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    provider = await _knowledge_provider(session, household_id=summary.id)
    result = await correct_fact(
        session,
        provider,
        ha_user_id=body.ha_user_id,
        fact_id=fact_id,
        value=body.value,
        confidence=body.confidence,
    )
    if isinstance(result, (Unmapped, FactNotFound)):
        await session.rollback()
        raise _fact_not_found()
    if isinstance(result, NotConfirmed):
        await session.rollback()
        raise _fact_not_confirmed()
    if isinstance(result, ProviderUnavailable):
        await session.rollback()
        raise _provider_unavailable()
    await session.commit()
    return KnowledgeFactPayload.from_record(result)


@router.delete("/knowledge/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def integration_delete_fact(
    fact_id: str, ha_user_id: HaUserIdQuery, _token: IntegrationToken, session: Session
) -> None:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    provider = await _knowledge_provider(session, household_id=summary.id)
    result = await delete_fact(session, provider, ha_user_id=ha_user_id, fact_id=fact_id)
    if isinstance(result, (Unmapped, FactNotFound)):
        await session.rollback()
        raise _fact_not_found()
    if isinstance(result, NotConfirmed):
        await session.rollback()
        raise _fact_not_confirmed()
    assert isinstance(result, KnowledgeDisposed)
    await session.commit()


class ToolPolicyPayload(BaseModel):
    permissions: dict[str, str]

    @classmethod
    def from_record(cls, policy: HomeAssistantToolPolicyRecord) -> ToolPolicyPayload:
        return cls(permissions=dict(policy.permissions))


class UpdateToolPolicyRequest(BaseModel):
    permissions: dict[str, str]


def _invalid_permission_value() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "code": "invalid_permission_value",
            "message": "Each permission must be one of: allow, approval_required, deny.",
        },
    )


@router.get("/settings/home-assistant-tool-policy", response_model=ToolPolicyPayload)
async def integration_get_tool_policy(_token: IntegrationToken, session: Session) -> ToolPolicyPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    policy = await get_or_create_tool_policy(session, household_id=summary.id)
    await session.commit()
    return ToolPolicyPayload.from_record(policy)


@router.patch("/settings/home-assistant-tool-policy", response_model=ToolPolicyPayload)
async def integration_update_tool_policy(
    body: UpdateToolPolicyRequest, _token: IntegrationToken, session: Session
) -> ToolPolicyPayload:
    """Gated by the integration bearer token alone, like ``/settings/assistant-policy`` -
    only the Kinward HA integration's own options flow calls this, and HA already
    restricts that to admins. Not yet surfaced in the options flow UI itself (Epic 7
    Story 7.3 v0 note) - callable today via this contract only.
    """
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    for value in body.permissions.values():
        if value not in ("allow", "approval_required", "deny"):
            raise _invalid_permission_value()
    policy = await update_tool_policy(session, household_id=summary.id, permissions=body.permissions)
    await session.commit()
    return ToolPolicyPayload.from_record(policy)


class RequestActionRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    assistant_id: str = Field(alias="assistantId", min_length=1, max_length=36)
    domain: str = Field(min_length=1, max_length=64)
    service: str = Field(min_length=1, max_length=64)
    entity_id: str = Field(alias="entityId", min_length=1, max_length=255)
    data: dict[str, Any] | None = None
    explanation: str = Field(min_length=1, max_length=1000)


class ActionResultPayload(BaseModel):
    outcome: str
    approval_id: str | None = Field(default=None, serialization_alias="approvalId")


class PendingActionPayload(BaseModel):
    id: str
    requested_by_person_id: str = Field(serialization_alias="requestedByPersonId")
    action: str
    explanation: str
    domain: str
    service: str
    entity_id: str = Field(serialization_alias="entityId")
    created_at: datetime = Field(serialization_alias="createdAt")
    expires_at: datetime | None = Field(serialization_alias="expiresAt")

    @classmethod
    def from_record(cls, approval: ApprovalRecord) -> PendingActionPayload:
        payload = approval.payload
        return cls(
            id=approval.id,
            requested_by_person_id=approval.requested_by_person_id,
            action=approval.action,
            explanation=approval.explanation,
            domain=payload.get("domain", ""),
            service=payload.get("service", ""),
            entity_id=payload.get("entity_id", ""),
            created_at=approval.created_at,
            expires_at=approval.expires_at,
        )


class ResolveActionRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)


def _approval_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "approval_not_found"})


def _resolution_blocked(error: ApprovalResolutionError) -> HTTPException:
    status_code = (
        status.HTTP_403_FORBIDDEN if error.code == "admin_required" else status.HTTP_409_CONFLICT
    )
    return HTTPException(status_code=status_code, detail={"code": error.code, "message": error.message})


@router.post("/actions", response_model=ActionResultPayload)
async def integration_request_action(
    body: RequestActionRequest, _token: IntegrationToken, session: Session, settings: AppSettings
) -> ActionResultPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    result = await request_action(
        session,
        household_id=summary.id,
        ha_user_id=body.ha_user_id,
        assistant_id=body.assistant_id,
        domain=body.domain,
        service=body.service,
        entity_id=body.entity_id,
        data=body.data,
        explanation=body.explanation,
        settings=settings,
    )
    if isinstance(result, (Unmapped, AddressedAssistantNotFound)):
        await session.rollback()
        raise _assistant_not_found()
    if isinstance(result, AccessDenied):
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "access_denied",
                "message": f"You don't have access to {result.assistant_name}.",
            },
        )
    if isinstance(result, InvalidTarget):
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_target", "message": result.message},
        )
    if isinstance(result, CapabilityDenied):
        await session.commit()
        return ActionResultPayload(outcome="denied")
    if isinstance(result, PendingApprovalCreated):
        await session.commit()
        return ActionResultPayload(outcome="pending_approval", approval_id=result.approval_id)
    if isinstance(result, Executed):
        await session.commit()
        return ActionResultPayload(outcome="executed")
    assert isinstance(result, Failed)
    await session.commit()
    return ActionResultPayload(outcome="failed")


@router.get("/actions", response_model=list[PendingActionPayload])
async def integration_list_pending_actions(
    _token: IntegrationToken, session: Session
) -> list[PendingActionPayload]:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    approvals = await list_pending_actions(session, household_id=summary.id)
    return [PendingActionPayload.from_record(approval) for approval in approvals]


async def _resolve_action(
    approval_id: str,
    body: ResolveActionRequest,
    session: AsyncSession,
    settings: Settings,
    *,
    decision: Literal["approve", "deny"],
) -> ActionResultPayload:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    result = await resolve_pending_action(
        session,
        household_id=summary.id,
        approval_id=approval_id,
        ha_user_id=body.ha_user_id,
        decision=decision,
        settings=settings,
    )
    if isinstance(result, (Unmapped, NotAdmin)):
        await session.rollback()
        raise _admin_required()
    if isinstance(result, ApprovalNotFound):
        await session.rollback()
        raise _approval_not_found()
    if isinstance(result, ApprovalResolutionError):
        await session.rollback()
        raise _resolution_blocked(result)
    if isinstance(result, Denied):
        await session.commit()
        return ActionResultPayload(outcome="denied")
    if isinstance(result, Executed):
        await session.commit()
        return ActionResultPayload(outcome="executed")
    assert isinstance(result, Failed)
    await session.commit()
    return ActionResultPayload(outcome="failed")


@router.post("/actions/{approval_id}/approve", response_model=ActionResultPayload)
async def integration_approve_action(
    approval_id: str, body: ResolveActionRequest, _token: IntegrationToken, session: Session, settings: AppSettings
) -> ActionResultPayload:
    return await _resolve_action(approval_id, body, session, settings, decision="approve")


@router.post("/actions/{approval_id}/deny", response_model=ActionResultPayload)
async def integration_deny_action(
    approval_id: str, body: ResolveActionRequest, _token: IntegrationToken, session: Session, settings: AppSettings
) -> ActionResultPayload:
    return await _resolve_action(approval_id, body, session, settings, decision="deny")
