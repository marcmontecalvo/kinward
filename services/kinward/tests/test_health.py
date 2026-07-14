from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from kinward.app import create_app
from kinward.config import Settings
from kinward.health import EXPECTED_SCHEMA_REVISION
from kinward.persistence.models import Base


async def _prepare_database(
    path: Path,
    *,
    revision: str = EXPECTED_SCHEMA_REVISION,
    heartbeat_at: datetime | None = None,
) -> Settings:
    settings = Settings(_env_file=None, database_url=f"sqlite+aiosqlite:///{path}")
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": revision},
        )
        if heartbeat_at is not None:
            await connection.execute(
                text(
                    "INSERT INTO worker_heartbeats (worker_name, heartbeat_at) "
                    "VALUES ('core', :heartbeat_at)"
                ),
                {"heartbeat_at": heartbeat_at},
            )
    await engine.dispose()
    return settings


async def _get_health(settings: Settings) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app(settings))
    async with httpx.AsyncClient(transport=transport, base_url="https://example.invalid") as client:
        return await client.get("/api/v1/health")


async def test_health_is_healthy_without_optional_providers(tmp_path: Path) -> None:
    settings = await _prepare_database(tmp_path / "healthy.db", heartbeat_at=datetime.now(UTC))

    response = await _get_health(settings)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "kinward"
    assert body["contractVersion"] == "v1"
    assert {component["state"] for component in body["core"].values()} == {"healthy"}
    assert set(body["capabilities"]) == {
        "model",
        "memory",
        "knowledge",
        "calendar",
        "homeAssistant",
    }
    assert {capability["state"] for capability in body["capabilities"].values()} == {
        "intentionally-disabled"
    }


async def test_empty_and_whitespace_provider_settings_are_intentionally_disabled(
    tmp_path: Path,
) -> None:
    database_settings = await _prepare_database(
        tmp_path / "empty-settings.db", heartbeat_at=datetime.now(UTC)
    )
    settings = Settings(
        _env_file=None,
        database_url=database_settings.database_url,
        model_provider="  ",
        memory_backend="none",
        honcho_url="",
        knowledge_backend="none",
        llm_wiki_url=" \t ",
        calendar_provider="\n",
        home_assistant_url="",
        home_assistant_token="   ",
    )

    response = await _get_health(settings)

    assert response.status_code == 200
    body = response.json()
    assert {capability["state"] for capability in body["capabilities"].values()} == {
        "intentionally-disabled"
    }
    assert {capability["reason"] for capability in body["capabilities"].values()} == {
        "not-configured"
    }


async def test_configured_providers_are_not_available_without_a_successful_check(
    tmp_path: Path,
) -> None:
    settings = await _prepare_database(tmp_path / "configured.db", heartbeat_at=datetime.now(UTC))
    settings = settings.model_copy(
        update={
            "model_provider": "configured-model",
            "memory_backend": "honcho",
            "honcho_url": "https://memory.example.invalid/private",
            "knowledge_backend": "llm_wiki",
            "llm_wiki_url": "https://knowledge.example.invalid/private",
            "calendar_provider": "configured-calendar",
            "home_assistant_url": "https://home.example.invalid/private",
            "home_assistant_token": "fictional-secret-token",
        }
    )

    response = await _get_health(settings)

    assert response.status_code == 200
    body = response.json()
    assert {capability["state"] for capability in body["capabilities"].values()} == {
        "unavailable"
    }
    serialized = json.dumps(body)
    for private_value in (
        "configured-model",
        "configured-calendar",
        "memory.example.invalid",
        "knowledge.example.invalid",
        "home.example.invalid",
        "fictional-secret-token",
        str(tmp_path),
        settings.database_url,
    ):
        assert private_value not in serialized


def test_worker_timing_requires_a_finite_stale_window_larger_than_the_interval() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            worker_heartbeat_interval_seconds=30,
            worker_stale_after_seconds=30,
        )
    with pytest.raises(ValidationError):
        Settings(_env_file=None, worker_heartbeat_interval_seconds=float("inf"))


async def test_partial_home_assistant_configuration_is_intentionally_disabled(
    tmp_path: Path,
) -> None:
    settings = await _prepare_database(
        tmp_path / "partial-ha.db", heartbeat_at=datetime.now(UTC)
    )
    settings = settings.model_copy(
        update={"home_assistant_url": "https://home.example.invalid/private"}
    )

    response = await _get_health(settings)

    assert response.json()["capabilities"]["homeAssistant"]["state"] == (
        "intentionally-disabled"
    )


async def test_incompatible_schema_is_reported_separately(tmp_path: Path) -> None:
    settings = await _prepare_database(
        tmp_path / "old.db",
        revision="000_retired_revision",
        heartbeat_at=datetime.now(UTC),
    )

    response = await _get_health(settings)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["core"]["database"]["state"] == "healthy"
    assert body["core"]["schema"]["state"] == "unhealthy"
    assert body["core"]["schema"]["reason"] == "schema-incompatible"


async def test_stale_worker_heartbeat_is_unhealthy(tmp_path: Path) -> None:
    settings = await _prepare_database(
        tmp_path / "stale.db",
        heartbeat_at=datetime.now(UTC) - timedelta(minutes=5),
    )

    response = await _get_health(settings)

    assert response.status_code == 503
    body = response.json()
    assert body["core"]["workerOutbox"] == {
        "state": "unhealthy",
        "reason": "worker-heartbeat-stale",
    }


async def test_missing_database_never_leaks_connection_details(tmp_path: Path) -> None:
    private_path = tmp_path / "missing" / "private.db"
    settings = Settings(_env_file=None, database_url=f"sqlite+aiosqlite:///{private_path}")

    response = await _get_health(settings)

    assert response.status_code == 503
    serialized = response.text
    assert str(private_path) not in serialized
    assert settings.database_url not in serialized
    assert response.json()["core"]["database"] == {
        "state": "unhealthy",
        "reason": "database-unreachable",
    }
