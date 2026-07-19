from __future__ import annotations

import secrets
from typing import Annotated, Literal, cast
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.accounts import (
    AccountsError,
    ExternalAccountView,
    build_authorize_url,
    complete_oauth_callback,
    disconnect_account,
    list_accounts,
    list_household_people,
)
from kinward.application.household_summary import fetch_household_summary
from kinward.config import Settings
from kinward.persistence.session import session_dependency
from kinward.web.accounts_setup_page import ACCOUNTS_SETUP_HTML

router = APIRouter(prefix="/api/v1/setup/accounts", tags=["accounts-setup"])
page_router = APIRouter(tags=["accounts-setup"])

Session = Annotated[AsyncSession, Depends(session_dependency)]

ProviderPath = Literal["google", "microsoft"]


def _settings_dependency(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


AppSettings = Annotated[Settings, Depends(_settings_dependency)]


def _household_not_configured() -> HTTPException:
    return HTTPException(status_code=409, detail={"code": "household_not_configured"})


def _setup_not_configured() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "accounts_setup_not_configured",
            "message": (
                "Set KINWARD_ACCOUNTS_SETUP_TOKEN and at least one provider's client "
                "credentials to enable account connections."
            ),
        },
    )


async def _require_setup_token(
    settings: AppSettings,
    x_accounts_setup_token: Annotated[str | None, Header()] = None,
) -> None:
    """Gates the accounts-setup page's API - a browser-navigated page has no way to
    send an integration bearer token or an HA-derived admin identity (see
    ``api/integration.py``'s ``_require_admin``), so this is a dedicated long-lived
    shared secret instead, entered once into the page and held in the browser's
    ``sessionStorage``. The OAuth callback route deliberately does *not* use this
    dependency - Google/Microsoft's redirect can't carry custom headers, and the
    single-use signed ``state`` parameter is that route's own proof of legitimacy.
    """
    if not settings.accounts_setup_enabled:
        raise _setup_not_configured()
    if not x_accounts_setup_token or not secrets.compare_digest(
        x_accounts_setup_token, settings.accounts_setup_token or ""
    ):
        raise HTTPException(status_code=401, detail={"code": "invalid_setup_token"})


RequireSetupToken = Depends(_require_setup_token)


class ProvidersResponse(BaseModel):
    google: bool
    microsoft: bool


@router.get("/providers", response_model=ProvidersResponse)
async def providers(settings: AppSettings) -> ProvidersResponse:
    """Unauthenticated by design - only reveals which providers are *configured*,
    never any secret, so the setup page can gray out unavailable buttons before the
    setup token is even entered.
    """
    return ProvidersResponse(google=settings.google_oauth_enabled, microsoft=settings.microsoft_oauth_enabled)


class PersonPayload(BaseModel):
    id: str
    display_name: str = Field(serialization_alias="displayName")


@router.get("/people", response_model=list[PersonPayload], dependencies=[RequireSetupToken])
async def people(session: Session) -> list[PersonPayload]:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    options = await list_household_people(session, household_id=summary.id)
    return [PersonPayload(id=option.id, display_name=option.display_name) for option in options]


class AccountPayload(BaseModel):
    id: str
    provider: str
    provider_account_email: str = Field(serialization_alias="providerAccountEmail")
    status: str
    owner_person_id: str = Field(serialization_alias="ownerPersonId")
    owner_display_name: str = Field(serialization_alias="ownerDisplayName")
    last_synced_at: str | None = Field(default=None, serialization_alias="lastSyncedAt")
    last_sync_error: str | None = Field(default=None, serialization_alias="lastSyncError")

    @classmethod
    def from_view(cls, view: ExternalAccountView) -> AccountPayload:
        return cls(
            id=view.id,
            provider=view.provider,
            provider_account_email=view.provider_account_email,
            status=view.status,
            owner_person_id=view.owner_person_id,
            owner_display_name=view.owner_display_name,
            last_synced_at=view.last_synced_at.isoformat() if view.last_synced_at else None,
            last_sync_error=view.last_sync_error,
        )


@router.get("", response_model=list[AccountPayload], dependencies=[RequireSetupToken])
async def accounts(session: Session) -> list[AccountPayload]:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    views = await list_accounts(session, household_id=summary.id)
    return [AccountPayload.from_view(view) for view in views]


class ConnectRequest(BaseModel):
    person_id: str = Field(alias="personId")


class ConnectResponse(BaseModel):
    authorize_url: str = Field(serialization_alias="authorizeUrl")


@router.post("/{provider}/connect", response_model=ConnectResponse, dependencies=[RequireSetupToken])
async def connect(
    provider: ProviderPath, body: ConnectRequest, session: Session, settings: AppSettings
) -> ConnectResponse:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    try:
        result = await build_authorize_url(
            session,
            household_id=summary.id,
            person_id=body.person_id,
            provider=provider,
            settings=settings,
        )
    except AccountsError as error:
        await session.rollback()
        raise HTTPException(
            status_code=422, detail={"code": error.code, "message": error.message}
        ) from None
    await session.commit()
    return ConnectResponse(authorize_url=result.url)


@router.get("/{provider}/callback", include_in_schema=False)
async def callback(
    provider: ProviderPath,
    session: Session,
    settings: AppSettings,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """The provider redirects the household member's browser here directly - no
    ``X-Accounts-Setup-Token`` header is possible on a top-level navigation, so this
    route is intentionally outside ``_require_setup_token``. The single-use, 10-minute
    ``state`` token (``OAuthConnectStateRecord``) is this route's own proof that the
    request traces back to a setup-token-authorized ``connect`` call.
    """
    if error or not code or not state:
        await session.rollback()
        message = error or "missing_code"
        return RedirectResponse(url=f"/setup/accounts?status=error&message={quote(message)}", status_code=303)
    try:
        result = await complete_oauth_callback(
            session, provider=provider, code=code, state=state, settings=settings
        )
    except AccountsError as exc:
        await session.rollback()
        return RedirectResponse(
            url=f"/setup/accounts?status=error&message={quote(exc.message)}", status_code=303
        )
    await session.commit()
    return RedirectResponse(
        url=(
            f"/setup/accounts?status=connected&provider={quote(result.provider)}"
            f"&email={quote(result.email)}"
        ),
        status_code=303,
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireSetupToken])
async def disconnect(account_id: str, session: Session, settings: AppSettings) -> Response:
    summary = await fetch_household_summary(session)
    if summary is None:
        raise _household_not_configured()
    removed = await disconnect_account(
        session, household_id=summary.id, account_id=account_id, settings=settings
    )
    if not removed:
        await session.rollback()
        raise HTTPException(status_code=404, detail={"code": "account_not_found"})
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@page_router.get("/setup/accounts", response_class=HTMLResponse, include_in_schema=False)
async def accounts_setup_page() -> HTMLResponse:
    return HTMLResponse(ACCOUNTS_SETUP_HTML)
