from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.bootstrap import (
    BootstrapCommand,
    BootstrapError,
    SelectedPet,
    SqlAlchemyBootstrapUnitOfWork,
    execute_bootstrap,
)
from kinward.config import Settings
from kinward.persistence.models import HouseholdRecord
from kinward.persistence.session import session_dependency

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


class PetInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=80)
    shared_facts: list[str] = Field(default_factory=list, max_length=20)


class BootstrapRequest(BaseModel):
    household_name: str = Field(min_length=1, max_length=120)
    fallback_assistant_name: str = Field(default="Kinward", min_length=1, max_length=120)
    pets: list[PetInput] = Field(default_factory=list, max_length=30)
    csrf_token: str = Field(min_length=24, max_length=256)


class SetupStatusResponse(BaseModel):
    configured: bool
    bootstrap_available: bool


class BootstrapResponse(BaseModel):
    household_id: str
    fallback_assistant_id: str


def _settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(
    settings: Annotated[Settings, Depends(_settings)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> SetupStatusResponse:
    configured = bool(await session.scalar(select(func.count()).select_from(HouseholdRecord)))
    return SetupStatusResponse(
        configured=configured,
        bootstrap_available=not configured and bool(settings.setup_authorization),
    )


@router.post("/household", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_household(
    body: BootstrapRequest,
    settings: Annotated[Settings, Depends(_settings)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    setup_authorization: Annotated[str, Header(alias="X-Setup-Authorization")],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=120)],
    csrf_header: Annotated[str, Header(alias="X-CSRF-Token", min_length=24, max_length=256)],
) -> BootstrapResponse:
    if csrf_header != body.csrf_token:
        raise HTTPException(status_code=403, detail={"code": "csrf_denied", "retryable": True})
    command = BootstrapCommand(
        household_name=body.household_name,
        fallback_assistant_name=body.fallback_assistant_name,
        pets=tuple(SelectedPet(item.display_name, item.species, tuple(item.shared_facts)) for item in body.pets),
        idempotency_key=idempotency_key,
        setup_authorization=setup_authorization,
    )
    try:
        result = await execute_bootstrap(
            SqlAlchemyBootstrapUnitOfWork(session),
            command,
            configured_authorization=settings.setup_authorization or "",
            authorization_ttl_seconds=settings.setup_authorization_ttl_seconds,
        )
    except BootstrapError as error:
        await session.rollback()
        raise HTTPException(
            status_code=409 if error.code in {"already_configured", "idempotency_conflict"} else 403,
            detail={"code": error.code, "message": error.message, "retryable": error.retryable},
        ) from None
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "bootstrap_conflict",
                "message": "Setup could not be committed safely. Retry or reset the empty deployment.",
                "retryable": True,
            },
        ) from None
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "bootstrap_failed",
                "message": "Setup was rolled back. Retry safely; reset the empty deployment if the problem continues.",
                "retryable": True,
            },
        ) from None
    return BootstrapResponse.model_validate(result)
