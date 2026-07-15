"""Add topics and topic_turns for the Kinward conversation lifecycle.

Revision ID: 004_conversation_topics
Revises: 003_ha_user_mappings
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_conversation_topics"
down_revision: str | None = "003_ha_user_mappings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "assistant_id", sa.String(length=36), sa.ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "topic_turns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("topic_turns")
    op.drop_table("topics")
