from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from kinward.config import Settings
from kinward.persistence.models import OutboxMessageRecord, WorkerHeartbeatRecord

EXPECTED_SCHEMA_REVISION = "006_ha_person_sync"
CORE_WORKER_NAME = "core"

CoreState = Literal["healthy", "unhealthy"]
CapabilityState = Literal[
    "available",
    "degraded",
    "unavailable",
    "intentionally-disabled",
    "stale",
    "reauthorization-required",
]


class CoreComponentHealth(BaseModel):
    state: CoreState
    reason: str | None = None


class CapabilityHealth(BaseModel):
    state: CapabilityState
    reason: str | None = None


class CoreHealth(BaseModel):
    application: CoreComponentHealth
    database: CoreComponentHealth
    schema_health: CoreComponentHealth = Field(serialization_alias="schema")
    bootstrap: CoreComponentHealth
    worker_outbox: CoreComponentHealth = Field(serialization_alias="workerOutbox")


class CapabilityHealthSet(BaseModel):
    model_capability: CapabilityHealth = Field(serialization_alias="model")
    memory: CapabilityHealth
    knowledge: CapabilityHealth
    calendar: CapabilityHealth
    home_assistant: CapabilityHealth = Field(serialization_alias="homeAssistant")


class HealthResponse(BaseModel):
    status: CoreState
    service: Literal["kinward"] = "kinward"
    contract_version: Literal["v1"] = Field(default="v1", serialization_alias="contractVersion")
    core: CoreHealth
    capabilities: CapabilityHealthSet


def _healthy() -> CoreComponentHealth:
    return CoreComponentHealth(state="healthy")


def _unhealthy(reason: str) -> CoreComponentHealth:
    return CoreComponentHealth(state="unhealthy", reason=reason)


def _capability(configured: bool) -> CapabilityHealth:
    if not configured:
        return CapabilityHealth(state="intentionally-disabled", reason="not-configured")
    return CapabilityHealth(state="unavailable", reason="capability-check-required")


def _has_value(value: str | None) -> bool:
    return bool(value and value.strip())


def _provider_is_configured(value: str) -> bool:
    return _has_value(value) and value.strip().lower() != "none"


def _capabilities(settings: Settings) -> CapabilityHealthSet:
    return CapabilityHealthSet(
        model_capability=_capability(_provider_is_configured(settings.model_provider)),
        memory=_capability(settings.memory_backend != "none" or _has_value(settings.honcho_url)),
        knowledge=_capability(
            settings.knowledge_backend != "none" or _has_value(settings.llm_wiki_url)
        ),
        calendar=_capability(_provider_is_configured(settings.calendar_provider)),
        home_assistant=_capability(settings.home_assistant_enabled),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def probe_health(settings: Settings) -> HealthResponse:
    application = _healthy()
    database = _unhealthy("database-unreachable")
    schema = _unhealthy("schema-unavailable")
    bootstrap = _unhealthy("bootstrap-unavailable")
    worker_outbox = _unhealthy("worker-outbox-unavailable")
    engine: AsyncEngine | None = None

    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            database = _healthy()

            try:
                revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
                schema = (
                    _healthy()
                    if revision == EXPECTED_SCHEMA_REVISION
                    else _unhealthy("schema-incompatible")
                )
            except SQLAlchemyError:
                schema = _unhealthy("schema-unavailable")

            try:
                household_count = await connection.scalar(text("SELECT count(*) FROM households"))
                bootstrap = (
                    _healthy()
                    if isinstance(household_count, int) and household_count <= 1
                    else _unhealthy("single-household-invariant")
                )
            except SQLAlchemyError:
                bootstrap = _unhealthy("bootstrap-unavailable")

            try:
                await connection.execute(select(OutboxMessageRecord.id).limit(1))
                heartbeat = await connection.scalar(
                    select(WorkerHeartbeatRecord.heartbeat_at).where(
                        WorkerHeartbeatRecord.worker_name == CORE_WORKER_NAME
                    )
                )
                if not isinstance(heartbeat, datetime):
                    worker_outbox = _unhealthy("worker-heartbeat-missing")
                elif _as_utc(heartbeat) < datetime.now(UTC) - timedelta(
                    seconds=settings.worker_stale_after_seconds
                ):
                    worker_outbox = _unhealthy("worker-heartbeat-stale")
                else:
                    worker_outbox = _healthy()
            except SQLAlchemyError:
                worker_outbox = _unhealthy("worker-outbox-unavailable")
    except (OSError, SQLAlchemyError):
        pass
    finally:
        if engine is not None:
            await engine.dispose()

    core = CoreHealth(
        application=application,
        database=database,
        schema_health=schema,
        bootstrap=bootstrap,
        worker_outbox=worker_outbox,
    )
    status: CoreState = (
        "healthy"
        if all(component.state == "healthy" for component in core.__dict__.values())
        else "unhealthy"
    )
    return HealthResponse(status=status, core=core, capabilities=_capabilities(settings))
