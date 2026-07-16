"""Allow a person to own more than one assistant; add assistant_policy.

Drops the single-owned-assistant constraint (epics.md Story 3.4 revision: a
person may have zero, one, or several personal assistants with distinct
personalities - no product-enforced limit). Adds assistant_policy: an
admin-editable, per-household cap (max_assistants_per_person) and an optional
admin-approval gate for creating additional assistants, both changed from the
Kinward integration's options flow in Home Assistant.

Revision ID: 008_multiple_assistants_per_person
Revises: 007_provider_settings
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_multiple_assistants_per_person"
down_revision: str | None = "007_provider_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.drop_constraint("uq_assistants_personal_owner", type_="unique")

    op.create_table(
        "assistant_policy",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("max_assistants_per_person", sa.Integer(), nullable=True),
        sa.Column(
            "require_admin_approval_for_creation",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("assistant_policy")
    with op.batch_alter_table("assistants") as batch_op:
        batch_op.create_unique_constraint("uq_assistants_personal_owner", ["owner_person_id"])
