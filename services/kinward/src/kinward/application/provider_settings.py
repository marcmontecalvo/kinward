from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import ProviderSettingsRecord


async def get_or_create_provider_settings(
    session: AsyncSession, *, household_id: str
) -> ProviderSettingsRecord:
    """Every household gets exactly one row, created lazily on first access.

    Everything defaults to "none"/unset, matching the truthful degraded state
    Kinward already reports when no provider is configured.
    """
    settings = await session.scalar(
        select(ProviderSettingsRecord).where(ProviderSettingsRecord.household_id == household_id)
    )
    if settings is not None:
        return settings
    settings = ProviderSettingsRecord(household_id=household_id)
    session.add(settings)
    await session.flush()
    return settings


def _normalize_optional(value: str | None) -> str | None:
    """An explicitly blank field clears the setting; anything else is used as-is."""
    if value is not None and not value.strip():
        return None
    return value


async def update_provider_settings(
    session: AsyncSession,
    *,
    household_id: str,
    model_provider: str | None = None,
    model_base_url: str | None = None,
    model_name: str | None = None,
    model_api_key: str | None = None,
    memory_backend: str | None = None,
    honcho_url: str | None = None,
    knowledge_backend: str | None = None,
    llm_wiki_url: str | None = None,
) -> ProviderSettingsRecord:
    """Partial update: a field left ``None`` (omitted) is left unchanged.

    A field explicitly passed as an empty string clears it (used for the
    optional url/name/key fields; the *_backend/model_provider labels are
    never blank - "none" is the off state for those).
    """
    settings = await get_or_create_provider_settings(session, household_id=household_id)
    if model_provider is not None:
        settings.model_provider = model_provider
    if model_base_url is not None:
        settings.model_base_url = _normalize_optional(model_base_url)
    if model_name is not None:
        settings.model_name = _normalize_optional(model_name)
    if model_api_key is not None:
        settings.model_api_key = _normalize_optional(model_api_key)
    if memory_backend is not None:
        settings.memory_backend = memory_backend
    if honcho_url is not None:
        settings.honcho_url = _normalize_optional(honcho_url)
    if knowledge_backend is not None:
        settings.knowledge_backend = knowledge_backend
    if llm_wiki_url is not None:
        settings.llm_wiki_url = _normalize_optional(llm_wiki_url)
    settings.record_version += 1
    await session.flush()
    return settings
