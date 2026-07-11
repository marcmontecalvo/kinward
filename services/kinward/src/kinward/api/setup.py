from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.domain.assistant_ownership import validate_owner_count
from kinward.persistence.models import AssistantRecord, HouseholdRecord, PersonRecord
from kinward.persistence.session import session_dependency

router = APIRouter(prefix="/api/setup", tags=["setup"])


class SetupStatusResponse(BaseModel):
    configured: bool


class HouseholdBootstrapRequest(BaseModel):
    household_name: str = Field(min_length=1, max_length=120)
    admin_name: str = Field(min_length=1, max_length=120)
    admin_email: EmailStr | None = None
    assistant_name: str = Field(min_length=1, max_length=120)
    assistant_personality: dict[str, Any] = Field(default_factory=dict)
    assistant_accent: str | None = Field(default=None, max_length=32)


class HouseholdBootstrapResponse(BaseModel):
    household_id: str
    admin_person_id: str
    assistant_id: str


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(session: AsyncSession = Depends(session_dependency)) -> SetupStatusResponse:
    household_count = await session.scalar(select(func.count()).select_from(HouseholdRecord))
    return SetupStatusResponse(configured=bool(household_count))


@router.post(
    "/household",
    response_model=HouseholdBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bootstrap_household(
    request: HouseholdBootstrapRequest,
    session: AsyncSession = Depends(session_dependency),
) -> HouseholdBootstrapResponse:
    household_count = await session.scalar(select(func.count()).select_from(HouseholdRecord))
    if household_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Kinward deployment already has a household.",
        )

    valid, violation = validate_owner_count(assistant_type="personal", owner_count=1)
    if not valid or violation is not None:
        raise HTTPException(status_code=500, detail="Assistant ownership invariant failed.")

    household = HouseholdRecord(name=request.household_name.strip())
    session.add(household)
    await session.flush()

    admin = PersonRecord(
        household_id=household.id,
        display_name=request.admin_name.strip(),
        role="admin",
        email=str(request.admin_email) if request.admin_email else None,
    )
    session.add(admin)
    await session.flush()

    assistant = AssistantRecord(
        household_id=household.id,
        owner_person_id=admin.id,
        name=request.assistant_name.strip(),
        kind="primary",
        personality=request.assistant_personality,
        accent=request.assistant_accent,
    )
    session.add(assistant)
    await session.commit()

    return HouseholdBootstrapResponse(
        household_id=household.id,
        admin_person_id=admin.id,
        assistant_id=assistant.id,
    )
