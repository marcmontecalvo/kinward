from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.application.integration_tokens import create_token
from kinward.config import Settings
from kinward.integrations import google_calendar
from kinward.persistence.models import Base, HouseholdRecord, PersonRecord
from kinward.persistence.session import session_dependency

ACCOUNTS_SETUP_TOKEN = "s" * 32


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "test",
        "google_client_id": "google-client-id",
        "google_client_secret": "google-client-secret",
        "oauth_redirect_base_url": "http://kinward.local:8000",
        "account_token_encryption_key": Fernet.generate_key().decode(),
        "accounts_setup_token": ACCOUNTS_SETUP_TOKEN,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


async def _client(settings: Settings | None = None):  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app = create_app(settings or _settings())
    app.dependency_overrides[session_dependency] = override_session
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return client, factory


async def _seed_household(factory) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        person = PersonRecord(
            household_id=household.id, display_name="Marc", role="admin", profile_kind="adult"
        )
        session.add(person)
        await session.commit()
        return household.id, person.id


def _setup_headers() -> dict[str, str]:
    return {"X-Accounts-Setup-Token": ACCOUNTS_SETUP_TOKEN}


async def _issue_integration_token(factory) -> str:  # type: ignore[no-untyped-def]
    async with factory() as session:
        _record, plaintext = await create_token(session, "Home Assistant")
        await session.commit()
    return plaintext


async def test_setup_page_is_served() -> None:
    client, _factory = await _client()
    async with client:
        response = await client.get("/setup/accounts")
        assert response.status_code == 200
        assert "Connect Accounts" in response.text


async def test_setup_api_is_unavailable_when_not_configured() -> None:
    client, _factory = await _client(_settings(accounts_setup_token=None))
    async with client:
        response = await client.get("/api/v1/setup/accounts/people", headers=_setup_headers())
        assert response.status_code == 503


async def test_setup_api_rejects_a_missing_or_wrong_token() -> None:
    client, _factory = await _client()
    async with client:
        response = await client.get("/api/v1/setup/accounts/people")
        assert response.status_code == 401
        response = await client.get(
            "/api/v1/setup/accounts/people", headers={"X-Accounts-Setup-Token": "wrong"}
        )
        assert response.status_code == 401


async def test_setup_api_lists_household_people() -> None:
    client, factory = await _client()
    async with client:
        _household_id, person_id = await _seed_household(factory)
        response = await client.get("/api/v1/setup/accounts/people", headers=_setup_headers())
        assert response.status_code == 200
        assert response.json() == [{"id": person_id, "displayName": "Marc"}]


async def test_connect_then_callback_then_list_then_disconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_exchange_code(**_kwargs: object) -> google_calendar.OAuthTokens:
        return google_calendar.OAuthTokens(
            access_token="access-1", refresh_token="refresh-1", expires_in=3600
        )

    async def fake_fetch_account_email(_access_token: str) -> str:
        return "marc@example.com"

    async def fake_revoke_token(_access_token: str) -> None:
        return None

    monkeypatch.setattr(google_calendar, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(google_calendar, "fetch_account_email", fake_fetch_account_email)
    monkeypatch.setattr(google_calendar, "revoke_token", fake_revoke_token)

    client, factory = await _client()
    async with client:
        _household_id, person_id = await _seed_household(factory)

        connect = await client.post(
            "/api/v1/setup/accounts/google/connect",
            headers=_setup_headers(),
            json={"personId": person_id},
        )
        assert connect.status_code == 200
        authorize_url = connect.json()["authorizeUrl"]
        state = parse_qs(urlparse(authorize_url).query)["state"][0]

        callback = await client.get(
            "/api/v1/setup/accounts/google/callback",
            params={"code": "auth-code", "state": state},
        )
        assert callback.status_code == 303
        location = callback.headers["location"]
        assert "status=connected" in location
        assert "provider=google" in location

        listing = await client.get("/api/v1/setup/accounts", headers=_setup_headers())
        assert listing.status_code == 200
        accounts = listing.json()
        assert len(accounts) == 1
        assert accounts[0]["providerAccountEmail"] == "marc@example.com"
        assert accounts[0]["status"] == "connected"
        account_id = accounts[0]["id"]

        # Also visible, sanitized, to the Kinward HA integration's own bearer-token endpoint.
        token = await _issue_integration_token(factory)
        integration_response = await client.get(
            "/api/v1/integration/accounts", headers={"Authorization": f"Bearer {token}"}
        )
        assert integration_response.status_code == 200
        assert integration_response.json()[0]["providerAccountEmail"] == "marc@example.com"

        disconnect = await client.delete(
            f"/api/v1/setup/accounts/{account_id}", headers=_setup_headers()
        )
        assert disconnect.status_code == 204

        listing_after = await client.get("/api/v1/setup/accounts", headers=_setup_headers())
        assert listing_after.json() == []


async def test_callback_with_an_unknown_state_redirects_to_an_error() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household(factory)
        callback = await client.get(
            "/api/v1/setup/accounts/google/callback",
            params={"code": "auth-code", "state": "bogus"},
        )
        assert callback.status_code == 303
        assert "status=error" in callback.headers["location"]
