import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from argon2 import PasswordHasher
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.application import bootstrap as bootstrap_module
from kinward.application.bootstrap import capability_hash
from kinward.config import Settings
from kinward.persistence.models import (
    AccountRecord,
    ActivityRecord,
    AssistantRecord,
    Base,
    BootstrapAttemptRecord,
    HouseholdRecord,
    OutboxMessageRecord,
    PersonRecord,
    PetRecord,
    SetupCapabilityRecord,
)
from kinward.persistence.session import session_dependency

AUTH = "fictional-setup-authorization-12345"
CSRF = "fictional-csrf-token-123456789"


async def _client(database_url: str = "sqlite+aiosqlite:///:memory:"):  # type: ignore[no-untyped-def]
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app = create_app(Settings(environment="test", setup_authorization=AUTH))
    app.dependency_overrides[session_dependency] = override_session
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return client, factory, engine


def _payload() -> dict[str, object]:
    return {
        "household_name": "Example House",
        "admin_name": "Example Adult",
        "admin_email": "adult@example.invalid",
        "password": "fictional-password-123",
        "assistant_name": "Atlas Example",
        "fallback_assistant_name": "Kinward Example",
        "profiles": [
            {"display_name": "Example Grownup", "kind": "adult"},
            {"display_name": "Example Child", "kind": "child"},
        ],
        "pets": [
            {
                "display_name": "Example Pet",
                "species": "robot dog",
                "shared_facts": ["Uses the fictional blue bowl"],
            }
        ],
        "csrf_token": CSRF,
    }


def _headers(key: str = "setup-request-0001") -> dict[str, str]:
    return {"X-Setup-Authorization": AUTH, "X-CSRF-Token": CSRF, "Idempotency-Key": key}


async def test_bootstrap_creates_complete_graph_and_exact_replay() -> None:
    client, factory, engine = await _client()
    async with client:
        status = await client.get("/api/v1/setup/status")
        assert status.json() == {"configured": False, "bootstrap_available": True}
        created = await client.post("/api/v1/setup/household", json=_payload(), headers=_headers())
        assert created.status_code == 201
        replay = await client.post("/api/v1/setup/household", json=_payload(), headers=_headers())
        assert replay.status_code == 201
        assert replay.json() == created.json()
        status = await client.get("/api/v1/setup/status")
        assert status.json() == {"configured": True, "bootstrap_available": False}

    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(HouseholdRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(PersonRecord)) == 3
        assistants = (await session.scalars(select(AssistantRecord))).all()
        assert len(assistants) == 2
        assert sum(item.owner_person_id is None for item in assistants) == 1
        pet = await session.scalar(select(PetRecord))
        assert pet is not None and pet.shared_facts == ["Uses the fictional blue bowl"]
        assert await session.scalar(select(func.count()).select_from(AccountRecord)) == 1
        account = await session.scalar(select(AccountRecord))
        assert account is not None
        assert "fictional-password-123" not in account.password_verifier
        assert PasswordHasher().verify(account.password_verifier, "fictional-password-123")
        assert await session.scalar(select(func.count()).select_from(ActivityRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(OutboxMessageRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(BootstrapAttemptRecord)) == 1
    await engine.dispose()


async def test_bootstrap_denies_csrf_authorization_and_conflicting_replay() -> None:
    client, factory, engine = await _client()
    async with client:
        denied = await client.post(
            "/api/v1/setup/household",
            json=_payload(),
            headers={**_headers(), "X-CSRF-Token": "different-fictional-csrf-123"},
        )
        assert denied.status_code == 403
        denied = await client.post(
            "/api/v1/setup/household",
            json=_payload(),
            headers={**_headers(), "X-Setup-Authorization": "wrong-fictional-authorization"},
        )
        assert denied.status_code == 403
        assert (await client.post("/api/v1/setup/household", json=_payload(), headers=_headers())).status_code == 201
        changed = _payload()
        changed["household_name"] = "Different Example House"
        conflict = await client.post("/api/v1/setup/household", json=changed, headers=_headers())
        assert conflict.status_code == 409

    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(HouseholdRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(ActivityRecord)) == 1
    await engine.dispose()


async def test_validation_never_echoes_password() -> None:
    client, _, engine = await _client()
    payload = _payload()
    payload["password"] = "tiny-secret"
    async with client:
        response = await client.post("/api/v1/setup/household", json=payload, headers=_headers())
        assert response.status_code == 422
        assert "tiny-secret" not in response.text
    await engine.dispose()


async def test_concurrent_exact_replay_creates_one_graph(tmp_path: Path) -> None:
    client, factory, engine = await _client(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap.db'}")
    async with client:
        first, second = await asyncio.gather(
            client.post("/api/v1/setup/household", json=_payload(), headers=_headers()),
            client.post("/api/v1/setup/household", json=_payload(), headers=_headers()),
        )
        assert first.status_code == second.status_code == 201
        assert first.json() == second.json()
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(HouseholdRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(AssistantRecord)) == 2
        assert await session.scalar(select(func.count()).select_from(BootstrapAttemptRecord)) == 1
    await engine.dispose()


async def test_failure_after_partial_flush_rolls_back_every_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, factory, engine = await _client()
    original_hasher = bootstrap_module.PASSWORD_HASHER

    class FailingHasher:
        def hash(self, _password: str) -> str:
            raise RuntimeError("synthetic hashing failure")

    monkeypatch.setattr(bootstrap_module, "PASSWORD_HASHER", FailingHasher())
    async with client:
        failed = await client.post("/api/v1/setup/household", json=_payload(), headers=_headers())
        assert failed.status_code == 500
        assert failed.json()["detail"]["code"] == "bootstrap_failed"
        async with factory() as session:
            for model in (
                HouseholdRecord,
                PersonRecord,
                AccountRecord,
                AssistantRecord,
                PetRecord,
                SetupCapabilityRecord,
                BootstrapAttemptRecord,
                ActivityRecord,
                OutboxMessageRecord,
            ):
                assert await session.scalar(select(func.count()).select_from(model)) == 0

        monkeypatch.setattr(bootstrap_module, "PASSWORD_HASHER", original_hasher)
        retried = await client.post(
            "/api/v1/setup/household", json=_payload(), headers=_headers()
        )
        assert retried.status_code == 201
    await engine.dispose()


@pytest.mark.parametrize("failure_point", [1, 2, 3, 4, "commit"])
async def test_each_persistence_stage_rolls_back_without_orphans(
    failure_point: int | str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, factory, engine = await _client()
    from sqlalchemy.ext.asyncio import AsyncSession

    original_flush = AsyncSession.flush
    original_commit = AsyncSession.commit
    calls = 0

    async def failing_flush(self: AsyncSession, objects=None) -> None:  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        if calls == failure_point:
            raise RuntimeError("synthetic persistence-stage failure")
        await original_flush(self, objects)

    async def failing_commit(self: AsyncSession) -> None:
        raise RuntimeError("synthetic commit failure")

    if failure_point == "commit":
        monkeypatch.setattr(AsyncSession, "commit", failing_commit)
    else:
        monkeypatch.setattr(AsyncSession, "flush", failing_flush)
    async with client:
        response = await client.post(
            "/api/v1/setup/household", json=_payload(), headers=_headers()
        )
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "bootstrap_failed"
    monkeypatch.setattr(AsyncSession, "flush", original_flush)
    monkeypatch.setattr(AsyncSession, "commit", original_commit)
    async with factory() as session:
        for model in (
            HouseholdRecord,
            PersonRecord,
            AccountRecord,
            AssistantRecord,
            PetRecord,
            SetupCapabilityRecord,
            BootstrapAttemptRecord,
            ActivityRecord,
            OutboxMessageRecord,
        ):
            assert await session.scalar(select(func.count()).select_from(model)) == 0
    await engine.dispose()


async def test_policy_conflict_changes_nothing() -> None:
    client, factory, engine = await _client()
    payload = _payload()
    payload["fallback_assistant_name"] = payload["assistant_name"]
    async with client:
        response = await client.post("/api/v1/setup/household", json=payload, headers=_headers())
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "assistant_name_conflict"
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(HouseholdRecord)) == 0
        assert await session.scalar(select(func.count()).select_from(SetupCapabilityRecord)) == 0
    await engine.dispose()


async def test_expired_capability_and_second_household_are_denied_safely() -> None:
    client, factory, engine = await _client()
    async with factory() as session:
        session.add(
            SetupCapabilityRecord(
                verifier_hash=capability_hash(AUTH),
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        await session.commit()
    async with client:
        expired = await client.post(
            "/api/v1/setup/household", json=_payload(), headers=_headers()
        )
        assert expired.status_code == 403
        assert expired.json()["detail"]["code"] == "setup_authorization_invalid"
        async with factory() as session:
            capability = await session.scalar(select(SetupCapabilityRecord))
            assert capability is not None
            await session.delete(capability)
            await session.commit()
        created = await client.post(
            "/api/v1/setup/household", json=_payload(), headers=_headers()
        )
        assert created.status_code == 201
        second = await client.post(
            "/api/v1/setup/household", json=_payload(), headers=_headers("setup-request-0002")
        )
        assert second.status_code == 409
        assert second.json()["detail"]["code"] == "already_configured"
        status = await client.get("/api/v1/setup/status")
        serialized = status.text
        assert AUTH not in serialized
        assert "password" not in serialized
        assert "verifier" not in serialized
    await engine.dispose()
