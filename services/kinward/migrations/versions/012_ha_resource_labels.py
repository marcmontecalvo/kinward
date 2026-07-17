"""Add home_assistant_resource_labels: household-language overrides for HA entities (Epic 7
Story 7.1).

Admin-editable, versioned per row (mirrors home_assistant_tool_policy's shape but keyed by
entity_id rather than a household singleton, since every entity may need its own override or
none at all). Not every entity gets a row - the application-layer fallback chain
(domain/household_resource_labels.resolve_label) uses HA's own friendly_name attribute, then
the raw entity_id, when no override exists here.

Revision ID: 012_ha_resource_labels
Revises: 011_knowledge_facts
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012_ha_resource_labels"
down_revision: str | None = "011_knowledge_facts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "home_assistant_resource_labels",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "household_id", "entity_id", name="uq_ha_resource_labels_entity"
        ),
    )


def downgrade() -> None:
    op.drop_table("home_assistant_resource_labels")
