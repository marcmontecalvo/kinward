"""Initial single-household schema.

Revision ID: 001_initial_single_household
Revises:
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_single_household"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("singleton_key", sa.Integer(), nullable=False, unique=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("singleton_key = 1", name="ck_households_singleton"),
    )
    op.create_table(
        "people",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("birth_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("profile_kind", sa.String(length=16), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("household_id", "email", name="uq_people_household_email"),
    )
    op.create_table(
        "assistants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("personality", sa.JSON(), nullable=False),
        sa.Column("accent", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("household_id", "name", name="uq_assistants_household_name"),
        sa.UniqueConstraint("owner_person_id", name="uq_assistants_personal_owner"),
        sa.CheckConstraint(
            "(kind = 'household-fallback' AND owner_person_id IS NULL) OR "
            "(kind = 'primary' AND owner_person_id IS NOT NULL)",
            name="ck_assistants_kind_owner",
        ),
    )
    op.create_index(
        "uq_assistants_household_fallback",
        "assistants",
        ["household_id"],
        unique=True,
        sqlite_where=sa.text("kind = 'household-fallback'"),
        postgresql_where=sa.text("kind = 'household-fallback'"),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_verifier", sa.Text(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "pets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("species", sa.String(length=80), nullable=False),
        sa.Column("shared_facts", sa.JSON(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "relationships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_kind", sa.String(length=16), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("relationship", sa.String(length=80), nullable=False),
        sa.Column("object_kind", sa.String(length=16), nullable=False),
        sa.Column("object_id", sa.String(length=36), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "household_id", "subject_kind", "subject_id", "relationship", "object_kind", "object_id",
            name="uq_relationship_fact",
        ),
    )
    op.create_table(
        "setup_capabilities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("verifier_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "bootstrap_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "surface_layouts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=120), nullable=False),
        sa.Column("surface_class", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "household_id",
            "scope",
            "scope_id",
            "surface_class",
            name="uq_surface_layout_scope",
        ),
    )
    op.create_table(
        "layout_activation_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by_person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "activity",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assistant_id", sa.String(length=36), sa.ForeignKey("assistants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("undo_token", sa.String(length=160), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "memory_index",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assistant_id", sa.String(length=36), sa.ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("privacy", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "worker_heartbeats",
        sa.Column("worker_name", sa.String(length=40), primary_key=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("worker_heartbeats")
    op.drop_table("outbox_messages")
    op.drop_table("memory_index")
    op.drop_table("activity")
    op.drop_table("approvals")
    op.drop_table("layout_activation_attempts")
    op.drop_table("surface_layouts")
    op.drop_table("bootstrap_attempts")
    op.drop_table("setup_capabilities")
    op.drop_table("relationships")
    op.drop_table("pets")
    op.drop_table("accounts")
    op.drop_table("assistants")
    op.drop_table("people")
    op.drop_table("households")
