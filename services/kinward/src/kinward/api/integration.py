from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.assistants import (
    AssistantNotFound,
    update_own_primary_assistant,
)
from kinward.application.authorization import NotAdmin, resolve_admin
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
from kinward.application.people import PersonNotFound, list_people, reclassify_person
from kinward.application.person_deletion import AdminInvariantBlocked
from kinward.application.person_deletion import Deleted as PersonDeleted
from kinward.application.person_deletion import delete_person
from kinward.application.pets import PetNotFound
from kinward.application.pets import Deleted as PetDeleted
from kinward.application.pets import create_pet, delete_pet, list_pets, update_pet
from kinward.persistence.models import AssistantRecord, PersonRecord, TopicRecord, TopicTurnRecord
from kinward.application.household_summary import fetch_household_summary
from kinward.application.people_sync import SyncedPerson, sync_people
from kinward.health import CapabilityState
from kinward.persistence.models import IntegrationTokenRecord
from kinward.persistence.session import session_dependency
from kinward.api.security import require_integration_token

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

IntegrationToken = Annotated[IntegrationTokenRecord, Depends(require_integration_token)]
Session = Annotated[AsyncSession, Depends(session_dependency)]


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

    @classmethod
    def from_record(cls, assistant: AssistantRecord) -> AssistantPayload:
        return cls(id=assistant.id, name=assistant.name, personality=dict(assistant.personality))


class UpdateOwnAssistantRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=120)
    personality: dict[str, Any] | None = None


def _assistant_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "assistant_not_found"})


@router.patch("/assistants/primary", response_model=AssistantPayload)
async def integration_update_own_assistant(
    body: UpdateOwnAssistantRequest, _token: IntegrationToken, session: Session
) -> AssistantPayload:
    result = await update_own_primary_assistant(
        session, ha_user_id=body.ha_user_id, name=body.name, personality=body.personality
    )
    if isinstance(result, (Unmapped, AssistantNotFound)):
        await session.rollback()
        raise _assistant_not_found()
    await session.commit()
    return AssistantPayload.from_record(result)


class ConversationRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, alias="conversationId", max_length=36)
    language: str = Field(default="en", min_length=2, max_length=16)


class ConversationResponse(BaseModel):
    conversation_id: str | None = Field(serialization_alias="conversationId")
    outcome: str
    response_text: str = Field(serialization_alias="responseText")
    mapped: bool


UNMAPPED_RESPONSE_TEXT = "This Home Assistant user isn't linked to a Kinward profile yet."


@router.post("/conversation", response_model=ConversationResponse)
async def integration_conversation(
    body: ConversationRequest, _token: IntegrationToken, session: Session
) -> ConversationResponse:
    result = await handle_conversation_request(
        session,
        ha_user_id=body.ha_user_id,
        text=body.text,
        conversation_id=body.conversation_id,
        language=body.language,
    )
    await session.commit()
    if isinstance(result, Unmapped):
        return ConversationResponse(
            conversation_id=None,
            outcome="unmapped",
            response_text=UNMAPPED_RESPONSE_TEXT,
            mapped=False,
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
