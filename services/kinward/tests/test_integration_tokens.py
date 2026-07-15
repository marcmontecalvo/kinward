from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.integration_tokens import (
    create_token,
    list_tokens,
    revoke_token,
    verify_token,
)
from kinward.persistence.models import Base


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def test_created_token_verifies_and_updates_last_used() -> None:
    factory = await _factory()
    async with factory() as session:
        record, plaintext = await create_token(session, "Home Assistant")
        await session.commit()
        assert record.last_used_at is None

        verified = await verify_token(session, plaintext)
        await session.commit()
        assert verified is not None
        assert verified.id == record.id
        assert verified.last_used_at is not None


async def test_unknown_token_does_not_verify() -> None:
    factory = await _factory()
    async with factory() as session:
        await create_token(session, "Home Assistant")
        await session.commit()

        assert await verify_token(session, "not-a-real-token") is None


async def test_revoked_token_does_not_verify() -> None:
    factory = await _factory()
    async with factory() as session:
        record, plaintext = await create_token(session, "Home Assistant")
        await session.commit()

        assert await revoke_token(session, record.id) is True
        await session.commit()

        assert await verify_token(session, plaintext) is None
        assert await revoke_token(session, record.id) is False


async def test_list_tokens_reports_all_created_tokens() -> None:
    factory = await _factory()
    async with factory() as session:
        await create_token(session, "Home Assistant")
        await create_token(session, "Second Client")
        await session.commit()

        records = await list_tokens(session)
        assert {record.name for record in records} == {"Home Assistant", "Second Client"}
