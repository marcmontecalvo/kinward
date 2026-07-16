"""Add provider_settings: admin-editable model/memory/knowledge connection settings.

Lets a household change what LLM provider and which of the two memory systems
(Honcho, llm_wiki) Kinward talks to from the Kinward integration's options flow
in Home Assistant, instead of only through backend deployment env vars
(epics.md Epic 2/4 buildable-now slice).

Revision ID: 007_provider_settings
Revises: 006_ha_person_sync
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_provider_settings"
down_revision: str | None = "006_ha_person_sync"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_settings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("model_provider", sa.String(length=32), nullable=False),
        sa.Column("model_base_url", sa.String(length=300), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("model_api_key", sa.String(length=300), nullable=True),
        sa.Column("memory_backend", sa.String(length=32), nullable=False),
        sa.Column("honcho_url", sa.String(length=300), nullable=True),
        sa.Column("knowledge_backend", sa.String(length=32), nullable=False),
        sa.Column("llm_wiki_url", sa.String(length=300), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("provider_settings")
