"""Add per-assistant access mode and allowlist (ADR-002).

Adds `access_mode` (`owner_only` | `household` | `allowlist`, default
`owner_only`) and `allowed_person_ids` to `assistants`, so a person besides
the owner may address an assistant under a deterministic, owner-controlled
rule - never affecting which conversational-memory peer is used (that's the
existing, unconditional (person, assistant) session keying) or tool
permissions, both separate concerns. The household-fallback assistant is
backfilled to `household` mode, matching its existing "anyone may address it"
behavior.

Revision ID: 009_assistant_access_modes
Revises: 008_multiple_assistants_per_person
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_assistant_access_modes"
down_revision: str | None = "008_multiple_assistants_per_person"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.add_column(
            sa.Column(
                "access_mode", sa.String(length=16), nullable=False, server_default="owner_only"
            )
        )
        batch_op.add_column(
            sa.Column(
                "allowed_person_ids", sa.JSON(), nullable=False, server_default="[]"
            )
        )
        batch_op.create_check_constraint(
            "ck_assistants_access_mode",
            "access_mode IN ('owner_only', 'household', 'allowlist')",
        )
    op.execute("UPDATE assistants SET access_mode = 'household' WHERE kind = 'household-fallback'")


def downgrade() -> None:
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.drop_constraint("ck_assistants_access_mode", type_="check")
        batch_op.drop_column("allowed_person_ids")
        batch_op.drop_column("access_mode")
