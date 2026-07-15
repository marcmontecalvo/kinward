"""Add ha_user_mappings for Home Assistant user-to-person identity mapping.

Revision ID: 003_ha_user_mappings
Revises: 002_integration_tokens
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_ha_user_mappings"
down_revision: str | None = "002_integration_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ha_user_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("ha_user_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ha_user_mappings")
