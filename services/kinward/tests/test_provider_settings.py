from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.provider_settings import (
    get_or_create_provider_settings,
    update_provider_settings,
)
from kinward.persistence.models import Base, HouseholdRecord


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_household(session) -> str:  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    await session.commit()
    return household.id


async def test_defaults_to_none_everywhere_until_configured() -> None:
    factory = await _factory()
    async with factory() as session:
        household_id = await _seed_household(session)
        settings = await get_or_create_provider_settings(session, household_id=household_id)
        assert settings.model_provider == "none"
        assert settings.model_base_url is None
        assert settings.memory_backend == "none"
        assert settings.knowledge_backend == "none"


async def test_get_or_create_is_idempotent() -> None:
    factory = await _factory()
    async with factory() as session:
        household_id = await _seed_household(session)
        first = await get_or_create_provider_settings(session, household_id=household_id)
        await session.commit()
        second = await get_or_create_provider_settings(session, household_id=household_id)
        assert first.id == second.id


async def test_partial_update_only_touches_passed_fields() -> None:
    factory = await _factory()
    async with factory() as session:
        household_id = await _seed_household(session)
        await update_provider_settings(
            session,
            household_id=household_id,
            model_provider="openai",
            model_base_url="https://api.openai.com/v1",
            model_name="gpt-5",
            model_api_key="secret",
        )
        await session.commit()

        updated = await update_provider_settings(
            session, household_id=household_id, memory_backend="honcho", honcho_url="http://honcho.invalid"
        )
        await session.commit()

        assert updated.model_provider == "openai"
        assert updated.model_base_url == "https://api.openai.com/v1"
        assert updated.model_name == "gpt-5"
        assert updated.model_api_key == "secret"
        assert updated.memory_backend == "honcho"
        assert updated.honcho_url == "http://honcho.invalid"


async def test_blank_string_clears_an_optional_field() -> None:
    factory = await _factory()
    async with factory() as session:
        household_id = await _seed_household(session)
        await update_provider_settings(
            session, household_id=household_id, model_base_url="https://api.openai.com/v1"
        )
        await session.commit()

        cleared = await update_provider_settings(session, household_id=household_id, model_base_url="")
        await session.commit()

        assert cleared.model_base_url is None
