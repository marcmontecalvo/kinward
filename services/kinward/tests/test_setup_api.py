import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.persistence.models import Base
from kinward.persistence.session import session_dependency


async def test_household_bootstrap_is_atomic_and_single_use() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[session_dependency] = override_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        status = await client.get("/api/setup/status")
        assert status.json() == {"configured": False}

        payload = {
            "household_name": "Example House",
            "admin_name": "Example Adult",
            "admin_email": "adult@example.invalid",
            "assistant_name": "Atlas",
            "assistant_personality": {"tone": "direct"},
        }
        created = await client.post("/api/setup/household", json=payload)
        assert created.status_code == 201
        assert set(created.json()) == {"household_id", "admin_person_id", "assistant_id"}

        status = await client.get("/api/setup/status")
        assert status.json() == {"configured": True}

        duplicate = await client.post("/api/setup/household", json=payload)
        assert duplicate.status_code == 409

    await engine.dispose()
