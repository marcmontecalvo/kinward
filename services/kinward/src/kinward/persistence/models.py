from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class HouseholdRecord(Base):
    __tablename__ = "households"
    __table_args__ = (CheckConstraint("singleton_key = 1", name="ck_households_singleton"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    singleton_key: Mapped[int] = mapped_column(default=1, nullable=False, unique=True)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    people: Mapped[list[PersonRecord]] = relationship(back_populates="household", cascade="all, delete-orphan")
    assistants: Mapped[list[AssistantRecord]] = relationship(back_populates="household", cascade="all, delete-orphan")


class PersonRecord(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    ha_person_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    ha_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    profile_kind: Mapped[str] = mapped_column(String(16), default="adult", nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="private-person", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    household: Mapped[HouseholdRecord] = relationship(back_populates="people")
    assistants: Mapped[list[AssistantRecord]] = relationship(back_populates="owner")


class AssistantRecord(Base):
    __tablename__ = "assistants"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="uq_assistants_household_name"),
        CheckConstraint(
            "(kind = 'household-fallback' AND owner_person_id IS NULL) OR "
            "(kind = 'primary' AND owner_person_id IS NOT NULL)",
            name="ck_assistants_kind_owner",
        ),
        Index(
            "uq_assistants_household_fallback",
            "household_id",
            unique=True,
            sqlite_where=text("kind = 'household-fallback'"),
            postgresql_where=text("kind = 'household-fallback'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    owner_person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    personality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    accent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="private-person", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    household: Mapped[HouseholdRecord] = relationship(back_populates="assistants")
    owner: Mapped[PersonRecord | None] = relationship(back_populates="assistants")


class AssistantPolicyRecord(Base):
    """Admin-editable household policy for creating additional owned assistants.

    One row per household (created lazily on first read), changed from the Kinward
    integration's options flow in Home Assistant, same as ``ProviderSettingsRecord``.
    """

    __tablename__ = "assistant_policy"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    max_assistants_per_person: Mapped[int | None] = mapped_column(nullable=True)
    require_admin_approval_for_creation: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class SurfaceLayoutRecord(Base):
    __tablename__ = "surface_layouts"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "scope",
            "scope_id",
            "surface_class",
            name="uq_surface_layout_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    surface_class: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class LayoutActivationAttemptRecord(Base):
    __tablename__ = "layout_activation_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


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
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
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


class OutboxMessageRecord(Base):
    """Durable hand-off seam; Story 1.1 intentionally defines no delivery semantics."""

    __tablename__ = "outbox_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class WorkerHeartbeatRecord(Base):
    __tablename__ = "worker_heartbeats"

    worker_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PetRecord(Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str] = mapped_column(String(80), nullable=False)
    shared_facts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class RelationshipRecord(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "subject_kind",
            "subject_id",
            "relationship",
            "object_kind",
            "object_id",
            name="uq_relationship_fact",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(80), nullable=False)
    object_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    object_id: Mapped[str] = mapped_column(String(36), nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class SetupCapabilityRecord(Base):
    __tablename__ = "setup_capabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    verifier_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class IntegrationTokenRecord(Base):
    __tablename__ = "integration_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class TopicRecord(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    assistant_id: Mapped[str] = mapped_column(ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="private-person", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    turns: Mapped[list[TopicTurnRecord]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class TopicTurnRecord(Base):
    __tablename__ = "topic_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="private-person", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    topic: Mapped[TopicRecord] = relationship(back_populates="turns")


class ProviderSettingsRecord(Base):
    """Admin-editable connection settings for the model/memory/knowledge providers.

    One row per household (created lazily on first read), so household
    operators can change what Kinward talks to from the Kinward integration's
    options flow in Home Assistant without touching backend deployment config.
    """

    __tablename__ = "provider_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    model_provider: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    model_base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_api_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    memory_backend: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    honcho_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    knowledge_backend: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    llm_wiki_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class BootstrapAttemptRecord(Base):
    __tablename__ = "bootstrap_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
