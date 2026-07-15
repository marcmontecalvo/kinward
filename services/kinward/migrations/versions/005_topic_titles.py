"""Add an optional title to topics for rename support (epics.md Story 2.4).

Revision ID: 005_topic_titles
Revises: 004_conversation_topics
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_topic_titles"
down_revision: str | None = "004_conversation_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("title", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "title")
