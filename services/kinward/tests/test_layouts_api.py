import asyncio
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.config import Settings
from kinward.persistence.models import (
    ActivityRecord,
    Base,
    HouseholdRecord,
    LayoutActivationAttemptRecord,
    OutboxMessageRecord,
    PersonRecord,
    SurfaceLayoutRecord,
)
from kinward.persistence.session import session_dependency


def _layout(layout_id: str = "layout-example-desktop") -> dict[str, object]:
    return {
        "schemaMajor": 1,
        "id": layout_id,
        "version": 1,
        "contextVersion": 1,
        "surfaceClass": "personal-desktop",
        "grid": {"columns": 12, "gapPx": 16},
        "instances": [
            {
                "id": "now-example",
                "type": "now",
                "version": 1,
                "title": "Now",
                "config": {},
                "column": 1,
                "row": 1,
                "columns": 7,
                "rows": 2,
            }
        ],
    }


def _payload(expected_version: int = 0, layout_id: str = "layout-example-desktop") -> dict[str, object]:
    return {
        "scope": "household-surface",
        "surfaceClass": "personal-desktop",
        "expectedVersion": expected_version,
        "layout": _layout(layout_id),
    }


async def _client(database_url: str = "sqlite+aiosqlite:///:memory:"):  # type: ignore[no-untyped-def]
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(HouseholdRecord(name="Example Household"))
        await session.commit()

    async def override_session():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app = create_app(Settings(environment="test"))
    app.dependency_overrides[session_dependency] = override_session
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return client, factory, engine


async def test_layout_activation_is_versioned_atomic_and_idempotent() -> None:
    client, factory, engine = await _client()
    headers = {"Idempotency-Key": "layout-request-0001"}
    async with client:
        created = await client.post("/api/v1/layouts/activate", json=_payload(), headers=headers)
        assert created.status_code == 200
        assert created.json()["assignment_version"] == 1
        queried = await client.get("/api/v1/layouts/active/personal-desktop")
        assert queried.status_code == 200
        assert queried.json()["layout"]["id"] == "layout-example-desktop"
        replay = await client.post("/api/v1/layouts/activate", json=_payload(), headers=headers)
        assert replay.json() == created.json()
        conflict_payload = _payload(layout_id="layout-conflicting-example")
        conflict = await client.post("/api/v1/layouts/activate", json=conflict_payload, headers=headers)
        assert conflict.status_code == 409
        stale = await client.post(
            "/api/v1/layouts/activate",
            json=_payload(expected_version=0, layout_id="layout-stale-example"),
            headers={"Idempotency-Key": "layout-request-0002"},
        )
        assert stale.status_code == 409
        updated = await client.post(
            "/api/v1/layouts/activate",
            json=_payload(expected_version=1, layout_id="layout-updated-example"),
            headers={"Idempotency-Key": "layout-request-0003"},
        )
        assert updated.status_code == 200
        assert updated.json()["assignment_version"] == 2

    async with factory() as session:
        record = await session.scalar(select(SurfaceLayoutRecord))
        assert record is not None
        assert record.name == "layout-updated-example"
        assert record.version == 2
        assert await session.scalar(select(func.count()).select_from(SurfaceLayoutRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(LayoutActivationAttemptRecord)) == 2
        assert await session.scalar(select(func.count()).select_from(ActivityRecord)) == 2
        assert await session.scalar(select(func.count()).select_from(OutboxMessageRecord)) == 2
    await engine.dispose()


async def test_invalid_activation_preserves_last_valid_and_sanitizes_error() -> None:
    client, factory, engine = await _client()
    async with client:
        assert (
            await client.post(
                "/api/v1/layouts/activate",
                json=_payload(),
                headers={"Idempotency-Key": "layout-request-valid"},
            )
        ).status_code == 200
        invalid = _payload(expected_version=1)
        layout = invalid["layout"]
        assert isinstance(layout, dict)
        instances = layout["instances"]
        assert isinstance(instances, list)
        assert isinstance(instances[0], dict)
        instances[0]["renderer"] = "private-provider-payload-example"
        rejected = await client.post(
            "/api/v1/layouts/activate",
            json=invalid,
            headers={"Idempotency-Key": "layout-request-invalid"},
        )
        assert rejected.status_code == 422
        assert "private-provider-payload-example" not in rejected.text
    async with factory() as session:
        record = await session.scalar(select(SurfaceLayoutRecord))
        assert record is not None and record.version == 1 and record.name == "layout-example-desktop"
        assert await session.scalar(select(func.count()).select_from(LayoutActivationAttemptRecord)) == 1
    await engine.dispose()


async def test_client_supplied_scope_identifier_never_creates_authority() -> None:
    client, factory, engine = await _client()
    async with factory() as session:
        household = await session.scalar(select(HouseholdRecord))
        assert household is not None
        person = PersonRecord(
            household_id=household.id,
            display_name="Example Adult",
            role="member",
            profile_kind="adult",
        )
        session.add(person)
        await session.commit()
        person_id = person.id
    payload = _payload()
    payload["scope"] = "person-surface"
    payload["scopeId"] = "00000000-0000-4000-8000-000000000099"
    async with client:
        rejected = await client.post(
            "/api/v1/layouts/activate",
            json=payload,
            headers={"Idempotency-Key": "layout-person-invalid"},
        )
        assert rejected.status_code == 422
        assert "server-derived authority" in rejected.text
        assert person_id not in rejected.text
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(SurfaceLayoutRecord)) == 0
    await engine.dispose()


async def test_concurrent_exact_activation_replays_once(tmp_path: Path) -> None:
    client, factory, engine = await _client(f"sqlite+aiosqlite:///{tmp_path / 'layouts.db'}")
    async with client:
        first, second = await asyncio.gather(
            client.post("/api/v1/layouts/activate", json=_payload(), headers={"Idempotency-Key": "layout-concurrent"}),
            client.post("/api/v1/layouts/activate", json=_payload(), headers={"Idempotency-Key": "layout-concurrent"}),
        )
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(SurfaceLayoutRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(LayoutActivationAttemptRecord)) == 1
    await engine.dispose()
