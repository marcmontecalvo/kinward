"""Sync people from HA person entities; drop local accounts and HA user mappings.

Kinward now has no identity system of its own: people are synced from Home
Assistant's `person` entities (see docs/pivot design session referenced in
epics.md Story 3.1-3.4). This drops the local email/password account model
and the separate ha_user_mappings table in favor of two nullable columns on
`people` keyed off HA's own stable person registry id.

Revision ID: 006_ha_person_sync
Revises: 005_topic_titles
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_ha_person_sync"
down_revision: str | None = "005_topic_titles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("people") as batch_op:
        batch_op.drop_constraint("uq_people_household_email", type_="unique")
        batch_op.drop_column("email")
        batch_op.add_column(sa.Column("ha_person_id", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("ha_user_id", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_people_ha_person_id", ["ha_person_id"])
        batch_op.create_unique_constraint("uq_people_ha_user_id", ["ha_user_id"])

    op.drop_table("ha_user_mappings")
    op.drop_table("accounts")


def downgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.String(length=36), sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_verifier", sa.Text(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
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

    with op.batch_alter_table("people") as batch_op:
        batch_op.drop_constraint("uq_people_ha_user_id", type_="unique")
        batch_op.drop_constraint("uq_people_ha_person_id", type_="unique")
        batch_op.drop_column("ha_user_id")
        batch_op.drop_column("ha_person_id")
        batch_op.add_column(sa.Column("email", sa.String(length=320), nullable=True))
        batch_op.create_unique_constraint("uq_people_household_email", ["household_id", "email"])
