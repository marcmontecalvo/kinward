from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.layouts import (
    ActivateLayoutCommand,
    LayoutActivationError,
    SqlAlchemyLayoutUnitOfWork,
    activate_layout,
    get_household_surface_layout,
)
from kinward.persistence.session import session_dependency

router = APIRouter(prefix="/api/v1/layouts", tags=["layouts"])

SurfaceClass = Literal["personal-mobile", "personal-tablet", "personal-desktop", "shared-kitchen", "shared-living-room"]
CardType = Literal["assistant-presence", "now", "briefing", "continue", "schedule", "house-status", "approval", "assistant-input"]


class NarrowWhenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    requires_touch: bool | None = Field(default=None, alias="requiresTouch")
    requires_keyboard: bool | None = Field(default=None, alias="requiresKeyboard")


class LayoutInstancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=80)
    type: CardType
    version: Literal[1]
    title: str = Field(min_length=1, max_length=120)
    config: dict[str, Any] = Field(default_factory=dict, max_length=0)
    column: int = Field(ge=1, le=24)
    row: int = Field(ge=1, le=100)
    columns: int = Field(ge=1, le=24)
    rows: int = Field(ge=1, le=24)
    narrow_when: NarrowWhenPayload | None = Field(default=None, alias="narrowWhen")


class GridPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    columns: int = Field(ge=1, le=24)
    gap_px: int = Field(ge=8, le=64, alias="gapPx")


class LayoutPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    schema_major: Literal[1] = Field(alias="schemaMajor")
    id: str = Field(min_length=1, max_length=120)
    version: int = Field(gt=0)
    context_version: int = Field(gt=0, alias="contextVersion")
    surface_class: SurfaceClass = Field(alias="surfaceClass")
    grid: GridPayload
    instances: list[LayoutInstancePayload] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_grid_and_instances(self) -> LayoutPayload:
        seen: set[str] = set()
        for instance in self.instances:
            if instance.id in seen:
                raise ValueError("layout instance IDs must be unique")
            seen.add(instance.id)
            if instance.column + instance.columns - 1 > self.grid.columns:
                raise ValueError("layout instance exceeds the grid")
        return self


class ActivateLayoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope: Literal["explicit-surface", "person-surface", "room-surface", "household-surface"]
    scope_id: str | None = Field(default=None, min_length=1, max_length=120, alias="scopeId")
    surface_class: SurfaceClass = Field(alias="surfaceClass")
    expected_version: int = Field(ge=0, alias="expectedVersion")
    layout: LayoutPayload

    @model_validator(mode="after")
    def validate_scope(self) -> ActivateLayoutRequest:
        if self.layout.surface_class != self.surface_class:
            raise ValueError("layout surface class must match the assignment")
        needs_id = self.scope != "household-surface"
        if needs_id != bool(self.scope_id):
            raise ValueError("scopeId is required only for explicit, person, and room scopes")
        if self.scope != "household-surface":
            raise ValueError("personal, room, and explicit scopes require server-derived authority")
        return self


class ActivateLayoutResponse(BaseModel):
    assignment_id: str
    assignment_version: int
    layout_id: str
    scope: str
    surface_class: str


class ActiveLayoutResponse(BaseModel):
    assignment_id: str
    assignment_version: int
    scope: str
    surface_class: str
    layout: LayoutPayload


@router.get("/active/{surface_class}", response_model=ActiveLayoutResponse)
async def active_layout(
    surface_class: SurfaceClass,
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ActiveLayoutResponse:
    result = await get_household_surface_layout(session, surface_class=surface_class)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "layout_not_found"})
    return ActiveLayoutResponse.model_validate(result)


@router.post("/activate", response_model=ActivateLayoutResponse, status_code=status.HTTP_200_OK)
async def activate(
    body: ActivateLayoutRequest,
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=120)],
) -> ActivateLayoutResponse:
    command = ActivateLayoutCommand(
        scope=body.scope,
        scope_id=body.scope_id or "",
        surface_class=body.surface_class,
        expected_version=body.expected_version,
        layout_id=body.layout.id,
        configuration=body.layout.model_dump(by_alias=True, mode="json"),
        idempotency_key=idempotency_key,
    )
    try:
        result = await activate_layout(SqlAlchemyLayoutUnitOfWork(session), command)
    except LayoutActivationError as error:
        await session.rollback()
        raise HTTPException(
            status_code=409 if error.code in {"idempotency_conflict", "version_conflict"} else 422,
            detail={"code": error.code, "message": error.message, "retryable": error.retryable},
        ) from None
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"code": "layout_activation_failed", "message": "The prior valid layout remains active.", "retryable": True},
        ) from None
    return ActivateLayoutResponse.model_validate(result)
