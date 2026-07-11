from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kinward.config import Settings, get_settings


def create_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    runtime = settings or get_settings()
    engine = create_async_engine(runtime.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def session_dependency() -> AsyncIterator[AsyncSession]:
    factory = create_session_factory()
    async with factory() as session:
        yield session
