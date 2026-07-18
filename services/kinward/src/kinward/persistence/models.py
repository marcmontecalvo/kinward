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
        CheckConstraint(
            "access_mode IN ('owner_only', 'household', 'allowlist')",
            name="ck_assistants_access_mode",
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
    # ADR-002 "V0 assistant access configuration": who besides the owner may address
    # this assistant at all. Never affects which conversational-memory peer is used
    # (that's the unconditional (person, assistant) session keying) or tool
    # permissions - a separate, still-unbuilt concern.
    access_mode: Mapped[str] = mapped_column(String(16), default="owner_only", nullable=False)
    allowed_person_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    # Epic 3 Story 3.7: references a kinward.visual_packs/<id>.json catalog entry, not a table.
    visual_pack_id: Mapped[str] = mapped_column(String(64), default="orb", nullable=False)
    # Epic 3 Story 3.5: not_started/in_progress/skipped/completed. Defaults to "completed" at the
    # Python/column level (see migration 014) so only explicit creation paths (people_sync,
    # create_additional_assistant) opt a *new* assistant into "not_started".
    interview_state: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)
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
    """A pending or resolved meaningful action (Epic 6; ADR-002 sec. 5's ``pending_action``).

    ``assistant_id`` and ``affected_person_id`` are nullable because this pass only
    builds ADR-002's capability-risk-tier case (Epic 7.3's HA device control - no
    resource owner exists to notify, so any admin resolves it via
    ``domain/pending_action.can_resolve_approval``); ADR-002's other case (a specific
    person's existing resource, e.g. a future calendar reschedule) would populate
    ``affected_person_id`` and use a different resolver. ``payload`` holds the
    requested HA ``domain``/``service``/``entity_id``/``data``.
    """

    __tablename__ = "approvals"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'approved', 'denied', 'expired', 'cancelled', 'executed', 'failed')",
            name="ck_approvals_state",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    requested_by_person_id: Mapped[str] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    assistant_id: Mapped[str | None] = mapped_column(ForeignKey("assistants.id", ondelete="SET NULL"), nullable=True)
    affected_person_id: Mapped[str | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    resolved_by_person_id: Mapped[str | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HomeAssistantToolPolicyRecord(Base):
    """Admin-editable per-household HA tool-capability permissions (ADR-002 sec. 4).

    One row per household (created lazily on first read, defaulted from
    ``domain.tool_permission.DEFAULT_TOOL_PERMISSIONS``), changed from the Kinward
    integration's options flow in Home Assistant, same shape as
    ``AssistantPolicyRecord``/``ProviderSettingsRecord``.
    """

    __tablename__ = "home_assistant_tool_policy"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    permissions: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class HomeAssistantResourceLabelRecord(Base):
    """Admin-editable household-language label override for one HA entity (Epic 7 Story 7.1:
    "ordinary outputs use household language... mapping changes are versioned").

    Not every entity has a row - only ones where the household wants to override HA's own
    ``friendly_name`` attribute for what Kinward says aloud; see
    ``domain.household_resource_labels.resolve_label`` for the fallback chain used when an
    entity has no override here.
    """

    __tablename__ = "home_assistant_resource_labels"
    __table_args__ = (
        UniqueConstraint("household_id", "entity_id", name="uq_ha_resource_labels_entity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )


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


class KnowledgeFactRecord(Base):
    """Kinward-side control/authorization/lifecycle row over a knowledge provider's body (AD-25).

    Tracks a fact through ``pending`` (inspection-only inferred observation, fixed
    30-day expiry) -> ``confirmed`` (durable fact) -> ``rejected``/``expired``/``deleted``
    (disposed; body removed or removal requested). ``deletion_status`` is a separate
    axis for when an external provider cannot delete its body immediately.
    """

    __tablename__ = "knowledge_facts"
    __table_args__ = (
        CheckConstraint(
            "knowledge_state IN ('pending', 'confirmed', 'rejected', 'expired', 'deleted')",
            name="ck_knowledge_facts_state",
        ),
        CheckConstraint(
            "deletion_status IN ('none', 'deletion_pending', 'externally_retained')",
            name="ck_knowledge_facts_deletion_status",
        ),
        Index("ix_knowledge_facts_owner_state", "owner_person_id", "knowledge_state"),
        Index("ix_knowledge_facts_recurrence", "household_id", "recurrence_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    owner_person_id: Mapped[str] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    predicate: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    privacy: Mapped[str] = mapped_column(String(16), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    recurrence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    knowledge_state: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    deletion_status: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    depends_on: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    external_fact_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="private-person", nullable=False)


class CalendarEntityRecord(Base):
    """Which Home Assistant ``calendar.*`` entities Kinward reads (Epic 5 Story 5.1:
    "Calendar entities can be enabled or disabled for Kinward independently").

    A row exists only once an entity has been explicitly enabled or disabled -
    absence means "not yet decided," treated as disabled by default so a newly
    discovered HA calendar isn't silently synced before a household chooses to
    include it.
    """

    __tablename__ = "calendar_entities"
    __table_args__ = (
        UniqueConstraint("household_id", "entity_id", name="uq_calendar_entities_entity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class CalendarEventObservationRecord(Base):
    """The last-known snapshot of one HA calendar event (Epic 5 Story 5.1's retained
    fields: entity identity, event identity, observed time, start/end, title,
    location, status, RSVP, freshness).

    This is Kinward's only memory of "what the event used to look like" - every sync
    pass diffs freshly-read HA calendar state against these rows
    (``domain/calendar_change_detection.py``) to decide whether a change is meaningful,
    then overwrites the row with the new snapshot. It is a cache of HA's own data, not
    an independent source of truth (AD-08's calendar freshness contract) - safe to
    regenerate by resyncing, never backed up as durable content.
    """

    __tablename__ = "calendar_event_observations"
    __table_args__ = (
        UniqueConstraint(
            "household_id", "entity_id", "event_uid", name="uq_calendar_event_observation"
        ),
        Index("ix_calendar_event_observations_household", "household_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_uid: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rsvp_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class AttentionItemRecord(Base):
    """A durable record that a meaningful calendar condition may need notice or action
    (Epic 5 Core Concepts). One row per logical calendar condition
    (``recurrence_key``) - repeated sync observation of the same condition updates
    this row rather than creating a duplicate.

    ``superseded_by_id`` preserves history when a materially different newer change
    replaces this item, mirroring ``knowledge_facts``' dependents-invalidation
    approach to lineage rather than deleting the superseded row.
    """

    __tablename__ = "attention_items"
    __table_args__ = (
        CheckConstraint(
            "state IN ('active', 'acknowledged', 'dismissed', 'resolved', 'expired', 'superseded')",
            name="ck_attention_items_state",
        ),
        CheckConstraint(
            "change_type IN "
            "('cancelled', 'time_changed', 'location_changed', 'overlap', 'back_to_back', 'rsvp_required')",
            name="ck_attention_items_change_type",
        ),
        Index("ix_attention_items_household_state", "household_id", "state"),
        Index("ix_attention_items_recurrence", "household_id", "recurrence_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_uid: Mapped[str] = mapped_column(String(300), nullable=False)
    change_type: Mapped[str] = mapped_column(String(24), nullable=False)
    recurrence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    event_starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("attention_items.id", ondelete="SET NULL"), nullable=True
    )
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="household-shared", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notified_record_version: Mapped[int | None] = mapped_column(nullable=True)


class BootstrapAttemptRecord(Base):
    __tablename__ = "bootstrap_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    record_version: Mapped[int] = mapped_column(default=1, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="system-operational", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
