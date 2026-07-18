"""Add assistant visual-identity catalog reference and interview state (Epic 3
Stories 3.5-3.7).

``visual_pack_id`` references a built-in catalog entry (``kinward.visual_packs``,
not a database table - the catalog is static, code-shipped data) and defaults to
``orb`` for every assistant, existing or new. ``interview_state`` tracks the
Story 3.5 conversational personality interview
(``not_started``/``in_progress``/``skipped``/``completed``); it defaults to
``completed`` at the column level so every assistant that already exists today is
treated as already onboarded - only ``people_sync.sync_people``'s new-person path
and ``assistants.create_additional_assistant`` explicitly start a fresh assistant
at ``not_started``, so the interview never retroactively hijacks an existing
assistant's next conversation turn.

Revision ID: 014_assistant_visual_identity
Revises: 013_calendar_attention
Create Date: 2026-07-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014_assistant_visual_identity"
down_revision: str | None = "013_calendar_attention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.add_column(
            sa.Column(
                "visual_pack_id", sa.String(length=64), nullable=False, server_default="orb"
            )
        )
        batch_op.add_column(
            sa.Column(
                "interview_state", sa.String(length=16), nullable=False, server_default="completed"
            )
        )
        batch_op.create_check_constraint(
            "ck_assistants_interview_state",
            "interview_state IN ('not_started', 'in_progress', 'skipped', 'completed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.drop_constraint("ck_assistants_interview_state", type_="check")
        batch_op.drop_column("interview_state")
        batch_op.drop_column("visual_pack_id")
