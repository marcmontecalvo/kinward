"""Add calendar_entities, calendar_event_observations, and attention_items (Epic 5:
briefings, calendar awareness, and proactive attention).

``calendar_entities`` tracks which HA ``calendar.*`` entities are enabled for Kinward.
``calendar_event_observations`` is the last-known snapshot of each event, diffed on
every sync pass to detect meaningful changes (AD-08's calendar freshness contract) -
a regenerable cache, not durable content. ``attention_items`` is the durable
active/acknowledged/dismissed/resolved/expired/superseded state machine, one row per
logical calendar condition (``recurrence_key``).

Revision ID: 013_calendar_attention
Revises: 012_ha_resource_labels
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013_calendar_attention"
down_revision: str | None = "012_ha_resource_labels"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calendar_entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("household_id", "entity_id", name="uq_calendar_entities_entity"),
    )

    op.create_table(
        "calendar_event_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("event_uid", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("rsvp_status", sa.String(length=32), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "household_id", "entity_id", "event_uid", name="uq_calendar_event_observation"
        ),
    )
    op.create_index(
        "ix_calendar_event_observations_household",
        "calendar_event_observations",
        ["household_id"],
    )

    op.create_table(
        "attention_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(length=36),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("event_uid", sa.String(length=300), nullable=False),
        sa.Column("change_type", sa.String(length=24), nullable=False),
        sa.Column("recurrence_key", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("event_starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "superseded_by_id",
            sa.String(length=36),
            sa.ForeignKey("attention_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_record_version", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "state IN ('active', 'acknowledged', 'dismissed', 'resolved', 'expired', 'superseded')",
            name="ck_attention_items_state",
        ),
        sa.CheckConstraint(
            "change_type IN "
            "('cancelled', 'time_changed', 'location_changed', 'overlap', 'back_to_back', 'rsvp_required')",
            name="ck_attention_items_change_type",
        ),
    )
    op.create_index(
        "ix_attention_items_household_state", "attention_items", ["household_id", "state"]
    )
    op.create_index(
        "ix_attention_items_recurrence", "attention_items", ["household_id", "recurrence_key"]
    )


def downgrade() -> None:
    op.drop_index("ix_attention_items_recurrence", table_name="attention_items")
    op.drop_index("ix_attention_items_household_state", table_name="attention_items")
    op.drop_table("attention_items")
    op.drop_index(
        "ix_calendar_event_observations_household", table_name="calendar_event_observations"
    )
    op.drop_table("calendar_event_observations")
    op.drop_table("calendar_entities")
