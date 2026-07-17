from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import HomeAssistantResourceLabelRecord


async def list_resource_labels(
    session: AsyncSession, *, household_id: str
) -> list[HomeAssistantResourceLabelRecord]:
    rows = await session.scalars(
        select(HomeAssistantResourceLabelRecord)
        .where(HomeAssistantResourceLabelRecord.household_id == household_id)
        .order_by(HomeAssistantResourceLabelRecord.entity_id)
    )
    return list(rows)


async def get_resource_label_overrides(session: AsyncSession, *, household_id: str) -> dict[str, str]:
    """entity_id -> admin-set label, for the conversation grounding path to resolve against
    (``domain.household_resource_labels.resolve_label``)."""
    rows = await list_resource_labels(session, household_id=household_id)
    return {row.entity_id: row.label for row in rows}


async def set_resource_label(
    session: AsyncSession, *, household_id: str, entity_id: str, label: str
) -> HomeAssistantResourceLabelRecord:
    """Create or update one entity's override label - lazily created, versioned per row
    (mirrors ``pending_actions.get_or_create_tool_policy``'s "created on first write" shape,
    but per-entity rather than a household singleton)."""
    existing = await session.scalar(
        select(HomeAssistantResourceLabelRecord).where(
            HomeAssistantResourceLabelRecord.household_id == household_id,
            HomeAssistantResourceLabelRecord.entity_id == entity_id,
        )
    )
    if existing is not None:
        existing.label = label
        existing.record_version += 1
        await session.flush()
        return existing
    record = HomeAssistantResourceLabelRecord(
        household_id=household_id, entity_id=entity_id, label=label
    )
    session.add(record)
    await session.flush()
    return record


async def delete_resource_label(session: AsyncSession, *, household_id: str, entity_id: str) -> bool:
    """Remove an override, falling back to ``friendly_name``/raw entity_id again. Returns
    ``False`` if no such override existed - a no-op, not an error."""
    existing = await session.scalar(
        select(HomeAssistantResourceLabelRecord).where(
            HomeAssistantResourceLabelRecord.household_id == household_id,
            HomeAssistantResourceLabelRecord.entity_id == entity_id,
        )
    )
    if existing is None:
        return False
    await session.delete(existing)
    await session.flush()
    return True
