"""Add knowledge_facts: Kinward-side lifecycle over provider-stored facts (AD-25, epics.md Story 4.3/4.4).

Tracks each fact through pending (inspection-only inferred observation, fixed
30-day expiry) -> confirmed (durable fact) -> rejected/expired/deleted, plus a
separate deletion_status axis for when an external provider cannot delete its
body immediately. The body itself continues to live with the configured
KnowledgeStoreProvider (llm_wiki); this table is the authorization/expiry/
recurrence-suppression/dependents-invalidation control layer on top of it.

Revision ID: 010_knowledge_facts
Revises: 009_assistant_access_modes
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_knowledge_facts"
down_revision: str | None = "009_assistant_access_modes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_facts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_person_id",
            sa.String(length=36),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("predicate", sa.String(length=200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("privacy", sa.String(length=16), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("source_version", sa.String(length=120), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recurrence_key", sa.String(length=64), nullable=False),
        sa.Column("knowledge_state", sa.String(length=16), nullable=False),
        sa.Column("deletion_status", sa.String(length=20), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("external_fact_id", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disposed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "knowledge_state IN ('pending', 'confirmed', 'rejected', 'expired', 'deleted')",
            name="ck_knowledge_facts_state",
        ),
        sa.CheckConstraint(
            "deletion_status IN ('none', 'deletion_pending', 'externally_retained')",
            name="ck_knowledge_facts_deletion_status",
        ),
    )
    op.create_index(
        "ix_knowledge_facts_owner_state", "knowledge_facts", ["owner_person_id", "knowledge_state"]
    )
    op.create_index(
        "ix_knowledge_facts_recurrence", "knowledge_facts", ["household_id", "recurrence_key"]
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_facts_recurrence", table_name="knowledge_facts")
    op.drop_index("ix_knowledge_facts_owner_state", table_name="knowledge_facts")
    op.drop_table("knowledge_facts")
