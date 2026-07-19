from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.config import Settings
from kinward.crypto import TokenDecryptionFailed, decrypt_token, encrypt_token
from kinward.integrations import google_calendar, microsoft_calendar
from kinward.integrations.oauth import OAuthExchangeError
from kinward.persistence.models import ExternalAccountRecord, OAuthConnectStateRecord, PersonRecord

Provider = Literal["google", "microsoft"]

# How long an in-flight connect attempt's state/PKCE handshake stays valid - long
# enough for a household member to actually complete the Google/Microsoft consent
# screen, short enough that a stale link can't be replayed.
STATE_TTL = timedelta(minutes=10)

# Refresh proactively rather than waiting for an expired-token API error - matches
# the margin most OAuth client libraries use.
REFRESH_MARGIN = timedelta(minutes=2)


class AccountsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    """SQLite round-trips ``DateTime(timezone=True)`` values as naive - normalize
    before comparing against a freshly-constructed aware ``datetime`` (same pattern as
    ``application/calendar.py``/``application/pending_actions.py``/``worker.py``).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def provider_enabled(settings: Settings, provider: Provider) -> bool:
    return settings.google_oauth_enabled if provider == "google" else settings.microsoft_oauth_enabled


def _hash_state(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _redirect_uri(settings: Settings, provider: Provider) -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/setup/accounts/{provider}/callback"


def _provider_scopes(provider: Provider) -> list[str]:
    return list(google_calendar.SCOPES if provider == "google" else microsoft_calendar.SCOPES)


@dataclass(frozen=True)
class PersonOption:
    id: str
    display_name: str


async def list_household_people(session: AsyncSession, *, household_id: str) -> list[PersonOption]:
    rows = await session.scalars(
        select(PersonRecord)
        .where(PersonRecord.household_id == household_id)
        .order_by(PersonRecord.display_name)
    )
    return [PersonOption(id=person.id, display_name=person.display_name) for person in rows]


@dataclass(frozen=True)
class AuthorizeUrl:
    url: str


async def build_authorize_url(
    session: AsyncSession,
    *,
    household_id: str,
    person_id: str,
    provider: Provider,
    settings: Settings,
) -> AuthorizeUrl:
    if not provider_enabled(settings, provider):
        raise AccountsError(
            "provider_not_configured", f"{provider.capitalize()} is not configured on this deployment."
        )
    person = await session.get(PersonRecord, person_id)
    if person is None or person.household_id != household_id:
        raise AccountsError("person_not_found", "That person was not found in this household.")

    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _pkce_pair()
    session.add(
        OAuthConnectStateRecord(
            household_id=household_id,
            person_id=person_id,
            provider=provider,
            state_hash=_hash_state(state),
            code_verifier=code_verifier,
            expires_at=_now() + STATE_TTL,
        )
    )
    await session.flush()

    redirect_uri = _redirect_uri(settings, provider)
    if provider == "google":
        assert settings.google_client_id
        url = google_calendar.build_authorize_url(
            client_id=settings.google_client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
        )
    else:
        assert settings.microsoft_client_id
        url = microsoft_calendar.build_authorize_url(
            tenant=settings.microsoft_tenant,
            client_id=settings.microsoft_client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
        )
    return AuthorizeUrl(url=url)


@dataclass(frozen=True)
class ConnectResult:
    account_id: str
    provider: Provider
    email: str


async def complete_oauth_callback(
    session: AsyncSession, *, provider: Provider, code: str, state: str, settings: Settings
) -> ConnectResult:
    if not provider_enabled(settings, provider):
        raise AccountsError(
            "provider_not_configured", f"{provider.capitalize()} is not configured on this deployment."
        )

    state_row = await session.scalar(
        select(OAuthConnectStateRecord).where(OAuthConnectStateRecord.state_hash == _hash_state(state))
    )
    if state_row is None or state_row.provider != provider:
        raise AccountsError("invalid_state", "This connection attempt is invalid or already used.")
    if state_row.consumed_at is not None:
        raise AccountsError("invalid_state", "This connection attempt was already used.")
    if _aware(state_row.expires_at) <= _now():
        raise AccountsError("expired_state", "This connection attempt expired - start again.")

    state_row.consumed_at = _now()
    await session.flush()

    redirect_uri = _redirect_uri(settings, provider)
    try:
        if provider == "google":
            assert settings.google_client_id and settings.google_client_secret
            tokens = await google_calendar.exchange_code(
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                redirect_uri=redirect_uri,
                code=code,
                code_verifier=state_row.code_verifier,
            )
            email = await google_calendar.fetch_account_email(tokens.access_token)
        else:
            assert settings.microsoft_client_id and settings.microsoft_client_secret
            tokens = await microsoft_calendar.exchange_code(
                tenant=settings.microsoft_tenant,
                client_id=settings.microsoft_client_id,
                client_secret=settings.microsoft_client_secret,
                redirect_uri=redirect_uri,
                code=code,
                code_verifier=state_row.code_verifier,
            )
            email = await microsoft_calendar.fetch_account_email(tokens.access_token)
    except OAuthExchangeError as exc:
        raise AccountsError("token_exchange_failed", str(exc)) from exc

    if not email:
        raise AccountsError(
            "profile_fetch_failed", "Could not read the connected account's email address."
        )

    existing = await session.scalar(
        select(ExternalAccountRecord).where(
            ExternalAccountRecord.household_id == state_row.household_id,
            ExternalAccountRecord.provider == provider,
            ExternalAccountRecord.owner_person_id == state_row.person_id,
        )
    )
    key = settings.account_token_encryption_key
    encrypted_access = encrypt_token(key, tokens.access_token)
    encrypted_refresh = (
        encrypt_token(key, tokens.refresh_token)
        if tokens.refresh_token
        else (existing.refresh_token_encrypted if existing else None)
    )
    expires_at = _now() + timedelta(seconds=tokens.expires_in)

    if existing is None:
        account = ExternalAccountRecord(
            household_id=state_row.household_id,
            owner_person_id=state_row.person_id,
            provider=provider,
            provider_account_email=email,
            scopes=_provider_scopes(provider),
            access_token_encrypted=encrypted_access,
            refresh_token_encrypted=encrypted_refresh,
            token_expires_at=expires_at,
            status="connected",
        )
        session.add(account)
    else:
        existing.provider_account_email = email
        existing.access_token_encrypted = encrypted_access
        existing.refresh_token_encrypted = encrypted_refresh
        existing.token_expires_at = expires_at
        existing.status = "connected"
        existing.last_sync_error = None
        existing.record_version += 1
        account = existing

    await session.flush()
    return ConnectResult(account_id=account.id, provider=provider, email=email)


@dataclass(frozen=True)
class ExternalAccountView:
    id: str
    provider: Provider
    provider_account_email: str
    status: str
    owner_person_id: str
    owner_display_name: str
    last_synced_at: datetime | None
    last_sync_error: str | None
    created_at: datetime


async def list_accounts(session: AsyncSession, *, household_id: str) -> list[ExternalAccountView]:
    rows = await session.scalars(
        select(ExternalAccountRecord)
        .where(ExternalAccountRecord.household_id == household_id)
        .order_by(ExternalAccountRecord.created_at)
    )
    accounts = list(rows)
    if not accounts:
        return []
    person_ids = {account.owner_person_id for account in accounts}
    people = await session.scalars(select(PersonRecord).where(PersonRecord.id.in_(person_ids)))
    names = {person.id: person.display_name for person in people}
    return [
        ExternalAccountView(
            id=account.id,
            provider=account.provider,  # type: ignore[arg-type]
            provider_account_email=account.provider_account_email,
            status=account.status,
            owner_person_id=account.owner_person_id,
            owner_display_name=names.get(account.owner_person_id, "Unknown"),
            last_synced_at=account.last_synced_at,
            last_sync_error=account.last_sync_error,
            created_at=account.created_at,
        )
        for account in accounts
    ]


async def disconnect_account(
    session: AsyncSession, *, household_id: str, account_id: str, settings: Settings
) -> bool:
    account = await session.get(ExternalAccountRecord, account_id)
    if account is None or account.household_id != household_id:
        return False
    if account.provider == "google":
        try:
            access_token = decrypt_token(settings.account_token_encryption_key, account.access_token_encrypted)
        except TokenDecryptionFailed:
            access_token = None
        if access_token:
            await google_calendar.revoke_token(access_token)
    await session.delete(account)
    await session.flush()
    return True


async def ensure_fresh_access_token(
    session: AsyncSession,
    *,
    account: ExternalAccountRecord,
    settings: Settings,
    now: datetime | None = None,
) -> str | None:
    """Return a valid access token for this account, refreshing it first if it's
    within ``REFRESH_MARGIN`` of expiry.

    On any failure (stored ciphertext no longer decrypts, no refresh token on file,
    the provider rejects the refresh - revoked consent, deleted app registration)
    the account is marked ``reauthorization_required`` and ``None`` is returned; the
    calendar sync pass then simply skips that account's events this pass, the same
    way it already treats HA being unreachable.

    ``now`` lets ``application/calendar.py::fetch_external_account_events`` (and
    tests) pin the reference time to the sync pass's own ``sync_time`` rather than
    wall-clock, the same way ``sync_household_calendars`` already threads its own
    ``now`` through.
    """
    moment = now or _now()
    key = settings.account_token_encryption_key
    try:
        access_token = decrypt_token(key, account.access_token_encrypted)
    except TokenDecryptionFailed:
        await _mark_reauthorization_required(session, account, "stored token could not be decrypted")
        return None

    if _aware(account.token_expires_at) - moment > REFRESH_MARGIN:
        return access_token

    if not account.refresh_token_encrypted:
        await _mark_reauthorization_required(session, account, "no refresh token on file")
        return None

    try:
        refresh_token = decrypt_token(key, account.refresh_token_encrypted)
        if account.provider == "google":
            assert settings.google_client_id and settings.google_client_secret
            tokens = await google_calendar.refresh_tokens(
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                refresh_token=refresh_token,
            )
        else:
            assert settings.microsoft_client_id and settings.microsoft_client_secret
            tokens = await microsoft_calendar.refresh_tokens(
                tenant=settings.microsoft_tenant,
                client_id=settings.microsoft_client_id,
                client_secret=settings.microsoft_client_secret,
                refresh_token=refresh_token,
            )
    except (OAuthExchangeError, TokenDecryptionFailed) as exc:
        await _mark_reauthorization_required(session, account, str(exc))
        return None

    account.access_token_encrypted = encrypt_token(key, tokens.access_token)
    if tokens.refresh_token:
        account.refresh_token_encrypted = encrypt_token(key, tokens.refresh_token)
    account.token_expires_at = moment + timedelta(seconds=tokens.expires_in)
    account.status = "connected"
    account.last_sync_error = None
    account.record_version += 1
    await session.flush()
    return tokens.access_token


async def _mark_reauthorization_required(
    session: AsyncSession, account: ExternalAccountRecord, error: str
) -> None:
    account.status = "reauthorization_required"
    account.last_sync_error = error
    account.record_version += 1
    await session.flush()
