from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.accounts import (
    AccountsError,
    build_authorize_url,
    complete_oauth_callback,
    disconnect_account,
    ensure_fresh_access_token,
    list_accounts,
    list_household_people,
)
from kinward.config import Settings
from kinward.crypto import decrypt_token, encrypt_token
from kinward.integrations import google_calendar
from kinward.persistence.models import (
    Base,
    ExternalAccountRecord,
    HouseholdRecord,
    OAuthConnectStateRecord,
    PersonRecord,
)

NOW = datetime(2026, 7, 19, 12, 0, 0, tzinfo=timezone.utc)


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "test",
        "database_url": "sqlite+aiosqlite:///:memory:",
        "google_client_id": "google-client-id",
        "google_client_secret": "google-client-secret",
        "oauth_redirect_base_url": "http://kinward.local:8000",
        "account_token_encryption_key": Fernet.generate_key().decode(),
        "accounts_setup_token": "s" * 32,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_person(session):  # type: ignore[no-untyped-def]
    household = HouseholdRecord(name="Example House")
    session.add(household)
    await session.flush()
    person = PersonRecord(
        household_id=household.id, display_name="Marc", role="admin", profile_kind="adult"
    )
    session.add(person)
    await session.flush()
    return household, person


def _state_from_url(url: str) -> str:
    return parse_qs(urlparse(url).query)["state"][0]


async def _fake_exchange_code(**_kwargs: object) -> google_calendar.OAuthTokens:
    return google_calendar.OAuthTokens(access_token="access-1", refresh_token="refresh-1", expires_in=3600)


async def _fake_fetch_account_email(_access_token: str) -> str:
    return "marc@example.com"


async def test_list_household_people_returns_display_names() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        options = await list_household_people(session, household_id=household.id)
    assert [option.id for option in options] == [person.id]
    assert options[0].display_name == "Marc"


async def test_build_authorize_url_happy_path() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        result = await build_authorize_url(
            session,
            household_id=household.id,
            person_id=person.id,
            provider="google",
            settings=settings,
        )
        await session.commit()
    assert result.url.startswith(google_calendar.AUTHORIZE_URL)
    assert "code_challenge=" in result.url


async def test_build_authorize_url_persists_a_single_use_state_row() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        await build_authorize_url(
            session,
            household_id=household.id,
            person_id=person.id,
            provider="google",
            settings=settings,
        )
        await session.commit()

        rows = list(await session.scalars(select(OAuthConnectStateRecord)))
        assert len(rows) == 1
        assert rows[0].provider == "google"
        assert rows[0].person_id == person.id
        assert rows[0].consumed_at is None


async def test_build_authorize_url_provider_not_configured() -> None:
    factory = await _factory()
    settings = _settings(google_client_id=None, google_client_secret=None)
    async with factory() as session:
        household, person = await _seed_person(session)
        with pytest.raises(AccountsError) as excinfo:
            await build_authorize_url(
                session,
                household_id=household.id,
                person_id=person.id,
                provider="google",
                settings=settings,
            )
    assert excinfo.value.code == "provider_not_configured"


async def test_build_authorize_url_unknown_person() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, _person = await _seed_person(session)
        with pytest.raises(AccountsError) as excinfo:
            await build_authorize_url(
                session,
                household_id=household.id,
                person_id="does-not-exist",
                provider="google",
                settings=settings,
            )
    assert excinfo.value.code == "person_not_found"


async def test_complete_oauth_callback_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = await _factory()
    settings = _settings()
    monkeypatch.setattr(google_calendar, "exchange_code", _fake_exchange_code)
    monkeypatch.setattr(google_calendar, "fetch_account_email", _fake_fetch_account_email)

    async with factory() as session:
        household, person = await _seed_person(session)
        authorize = await build_authorize_url(
            session,
            household_id=household.id,
            person_id=person.id,
            provider="google",
            settings=settings,
        )
        await session.commit()
        state = _state_from_url(authorize.url)

        result = await complete_oauth_callback(
            session, provider="google", code="auth-code", state=state, settings=settings
        )
        await session.commit()

        assert result.email == "marc@example.com"
        rows = list(await session.scalars(select(ExternalAccountRecord)))
        assert len(rows) == 1
        assert rows[0].provider_account_email == "marc@example.com"
        assert rows[0].owner_person_id == person.id
        # Tokens are encrypted at rest, never the plaintext value the provider returned.
        assert rows[0].access_token_encrypted != "access-1"

        state_row = (await session.scalars(select(OAuthConnectStateRecord))).one()
        assert state_row.consumed_at is not None


async def test_complete_oauth_callback_rejects_an_unknown_state() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        with pytest.raises(AccountsError) as excinfo:
            await complete_oauth_callback(
                session, provider="google", code="auth-code", state="bogus-state", settings=settings
            )
    assert excinfo.value.code == "invalid_state"


async def test_complete_oauth_callback_rejects_a_reused_state(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = await _factory()
    settings = _settings()
    monkeypatch.setattr(google_calendar, "exchange_code", _fake_exchange_code)
    monkeypatch.setattr(google_calendar, "fetch_account_email", _fake_fetch_account_email)

    async with factory() as session:
        household, person = await _seed_person(session)
        authorize = await build_authorize_url(
            session,
            household_id=household.id,
            person_id=person.id,
            provider="google",
            settings=settings,
        )
        await session.commit()
        state = _state_from_url(authorize.url)

        await complete_oauth_callback(
            session, provider="google", code="auth-code", state=state, settings=settings
        )
        await session.commit()

        with pytest.raises(AccountsError) as excinfo:
            await complete_oauth_callback(
                session, provider="google", code="auth-code", state=state, settings=settings
            )
    assert excinfo.value.code == "invalid_state"


async def test_complete_oauth_callback_rejects_an_expired_state() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        authorize = await build_authorize_url(
            session,
            household_id=household.id,
            person_id=person.id,
            provider="google",
            settings=settings,
        )
        state_row = (await session.scalars(select(OAuthConnectStateRecord))).one()
        state_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await session.commit()
        state = _state_from_url(authorize.url)

        with pytest.raises(AccountsError) as excinfo:
            await complete_oauth_callback(
                session, provider="google", code="auth-code", state=state, settings=settings
            )
    assert excinfo.value.code == "expired_state"


async def _seed_connected_account(session, *, household_id: str, owner_person_id: str, settings: Settings, **overrides):  # type: ignore[no-untyped-def]
    values: dict[str, object] = {
        "household_id": household_id,
        "owner_person_id": owner_person_id,
        "provider": "google",
        "provider_account_email": "marc@example.com",
        "scopes": [],
        "access_token_encrypted": encrypt_token(settings.account_token_encryption_key, "cached-access"),
        "refresh_token_encrypted": encrypt_token(settings.account_token_encryption_key, "cached-refresh"),
        "token_expires_at": NOW + timedelta(hours=1),
        "status": "connected",
    }
    values.update(overrides)
    account = ExternalAccountRecord(**values)  # type: ignore[arg-type]
    session.add(account)
    await session.flush()
    return account


async def test_ensure_fresh_access_token_returns_the_cached_token_when_not_near_expiry() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        account = await _seed_connected_account(
            session, household_id=household.id, owner_person_id=person.id, settings=settings
        )
        token = await ensure_fresh_access_token(session, account=account, settings=settings, now=NOW)
    assert token == "cached-access"
    assert account.status == "connected"


async def test_ensure_fresh_access_token_refreshes_when_near_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_refresh(**_kwargs: object) -> google_calendar.OAuthTokens:
        return google_calendar.OAuthTokens(
            access_token="new-access", refresh_token="new-refresh", expires_in=3600
        )

    monkeypatch.setattr(google_calendar, "refresh_tokens", fake_refresh)

    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        account = await _seed_connected_account(
            session,
            household_id=household.id,
            owner_person_id=person.id,
            settings=settings,
            token_expires_at=NOW + timedelta(seconds=30),
        )
        token = await ensure_fresh_access_token(session, account=account, settings=settings, now=NOW)
    assert token == "new-access"
    assert account.status == "connected"
    assert decrypt_token(settings.account_token_encryption_key, account.access_token_encrypted) == "new-access"


async def test_ensure_fresh_access_token_marks_reauthorization_required_on_refresh_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_refresh(**_kwargs: object) -> google_calendar.OAuthTokens:
        raise google_calendar.OAuthExchangeError("invalid_grant")

    monkeypatch.setattr(google_calendar, "refresh_tokens", fake_refresh)

    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        account = await _seed_connected_account(
            session,
            household_id=household.id,
            owner_person_id=person.id,
            settings=settings,
            token_expires_at=NOW - timedelta(seconds=1),
        )
        token = await ensure_fresh_access_token(session, account=account, settings=settings, now=NOW)
    assert token is None
    assert account.status == "reauthorization_required"
    assert account.last_sync_error is not None


async def test_ensure_fresh_access_token_without_a_refresh_token_requires_reauthorization() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        account = await _seed_connected_account(
            session,
            household_id=household.id,
            owner_person_id=person.id,
            settings=settings,
            token_expires_at=NOW - timedelta(seconds=1),
            refresh_token_encrypted=None,
        )
        token = await ensure_fresh_access_token(session, account=account, settings=settings, now=NOW)
    assert token is None
    assert account.status == "reauthorization_required"


async def test_list_accounts_reports_owner_display_name() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        await _seed_connected_account(
            session, household_id=household.id, owner_person_id=person.id, settings=settings
        )
        views = await list_accounts(session, household_id=household.id)
    assert len(views) == 1
    assert views[0].owner_display_name == "Marc"
    assert views[0].provider_account_email == "marc@example.com"


async def test_disconnect_account_removes_the_row_and_best_effort_revokes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revoked: list[str] = []

    async def fake_revoke(token: str) -> None:
        revoked.append(token)

    monkeypatch.setattr(google_calendar, "revoke_token", fake_revoke)

    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, person = await _seed_person(session)
        account = await _seed_connected_account(
            session, household_id=household.id, owner_person_id=person.id, settings=settings
        )
        await session.commit()
        account_id = account.id

        removed = await disconnect_account(
            session, household_id=household.id, account_id=account_id, settings=settings
        )
        await session.commit()

    assert removed is True
    assert revoked == ["cached-access"]


async def test_disconnect_account_returns_false_for_an_unknown_id() -> None:
    factory = await _factory()
    settings = _settings()
    async with factory() as session:
        household, _person = await _seed_person(session)
        removed = await disconnect_account(
            session, household_id=household.id, account_id="does-not-exist", settings=settings
        )
    assert removed is False
