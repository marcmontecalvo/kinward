from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from kinward.persistence.models import TopicRecord, TopicTurnRecord
from kinward.application.ha_user_mappings import (
    MappingError,
    list_mappings,
    remove_mapping,
    upsert_mapping,
)
from kinward.application.household_summary import fetch_household_summary
from kinward.application.people import list_account_bearing_people
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
    people = await list_account_bearing_people(session)
    return [PersonPayload(id=person.id, display_name=person.display_name) for person in people]


class HaUserMappingPayload(BaseModel):
    ha_user_id: str = Field(serialization_alias="haUserId")
    person_id: str = Field(serialization_alias="personId")


class HaUserMappingRequest(BaseModel):
    ha_user_id: str = Field(alias="haUserId", min_length=1, max_length=64)
    person_id: str = Field(alias="personId", min_length=1, max_length=36)


@router.get("/ha-user-mappings", response_model=list[HaUserMappingPayload])
async def get_ha_user_mappings(
    _token: IntegrationToken, session: Session
) -> list[HaUserMappingPayload]:
    records = await list_mappings(session)
    return [
        HaUserMappingPayload(ha_user_id=record.ha_user_id, person_id=record.person_id)
        for record in records
    ]


@router.put("/ha-user-mappings", response_model=list[HaUserMappingPayload])
async def put_ha_user_mappings(
    body: list[HaUserMappingRequest],
    _token: IntegrationToken,
    session: Session,
) -> list[HaUserMappingPayload]:
    try:
        for item in body:
            await upsert_mapping(session, ha_user_id=item.ha_user_id, person_id=item.person_id)
    except MappingError as error:
        await session.rollback()
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": error.message}
        ) from None
    await session.commit()
    records = await list_mappings(session)
    return [
        HaUserMappingPayload(ha_user_id=record.ha_user_id, person_id=record.person_id)
        for record in records
    ]


@router.delete("/ha-user-mappings/{ha_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ha_user_mapping(ha_user_id: str, _token: IntegrationToken, session: Session) -> None:
    await remove_mapping(session, ha_user_id=ha_user_id)
    await session.commit()


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
