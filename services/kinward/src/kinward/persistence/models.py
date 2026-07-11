from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class HouseholdRecord(Base):
    __tablename__ = "households"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    people: Mapped[list[PersonRecord]] = relationship(back_populates="household", cascade="all, delete-orphan")
    assistants: Mapped[list[AssistantRecord]] = relationship(back_populates="household", cascade="all, delete-orphan")


class PersonRecord(Base):
    __tablename__ = "people"
    __table_args__ = (UniqueConstraint("household_id", "email", name="uq_people_household_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    household: Mapped[HouseholdRecord] = relationship(back_populates="people")
    assistants: Mapped[list[AssistantRecord]] = relationship(back_populates="owner")


class AssistantRecord(Base):
    __tablename__ = "assistants"
    __table_args__ = (UniqueConstraint("household_id", "name", name="uq_assistants_household_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    owner_person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    personality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    accent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    household: Mapped[HouseholdRecord] = relationship(back_populates="assistants")
    owner: Mapped[PersonRecord | None] = relationship(back_populates="assistants")


class SurfaceLayoutRecord(Base):
    __tablename__ = "surface_layouts"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "owner_person_id",
            "room_id",
            "surface_class",
            "name",
            name="uq_surface_layout_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    owner_person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=True)
    room_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    surface_class: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="default")
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    requested_by_person_id: Mapped[str] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ActivityRecord(Base):
    __tablename__ = "activity"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    assistant_id: Mapped[str | None] = mapped_column(ForeignKey("assistants.id", ondelete="SET NULL"), nullable=True)
    person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    undo_token: Mapped[str | None] = mapped_column(String(160), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class MemoryIndexRecord(Base):
    __tablename__ = "memory_index"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    assistant_id: Mapped[str] = mapped_column(ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    privacy: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
