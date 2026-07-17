"""Wire up the meaningful-action approval state machine (Epic 6; ADR-002 sec. 5).

Extends the previously schema-only `approvals` table with the fields the v0
capability-risk-tier slice needs: `assistant_id`/`affected_person_id` (nullable -
this pass only builds the no-resource-owner HA device-control case, so
`affected_person_id` stays unused until a future person-owned-resource case, e.g.
calendar, populates it), `resolved_by_person_id`, `expires_at`, and the
`record_version`/`classification` pair every other lifecycle-tracked table carries.
Adds a full CHECK constraint on `state` covering ADR-002's seven-value enum
(previously unconstrained). Adds `home_assistant_tool_policy`, the admin-editable
per-household capability permission table (ADR-002 sec. 4), mirroring
`assistant_policy`'s singleton-per-household shape.

Revision ID: 010_meaningful_action_approvals
Revises: 009_assistant_access_modes
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_meaningful_action_approvals"
down_revision: str | None = "009_assistant_access_modes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("approvals") as batch_op:
        batch_op.add_column(
            sa.Column(
                "assistant_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "assistants.id", ondelete="SET NULL", name="fk_approvals_assistant_id_assistants"
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "affected_person_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "people.id", ondelete="SET NULL", name="fk_approvals_affected_person_id_people"
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "resolved_by_person_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "people.id", ondelete="SET NULL", name="fk_approvals_resolved_by_person_id_people"
                ),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("record_version", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.add_column(
            sa.Column(
                "classification",
                sa.String(length=32),
                nullable=False,
                server_default="system-operational",
            )
        )
        batch_op.create_check_constraint(
            "ck_approvals_state",
            "state IN ('pending', 'approved', 'denied', 'expired', 'cancelled', 'executed', 'failed')",
        )

    op.create_table(
        "home_assistant_tool_policy",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("home_assistant_tool_policy")
    with op.batch_alter_table("approvals") as batch_op:
        batch_op.drop_constraint("ck_approvals_state", type_="check")
        batch_op.drop_column("classification")
        batch_op.drop_column("record_version")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("resolved_by_person_id")
        batch_op.drop_column("affected_person_id")
        batch_op.drop_column("assistant_id")
