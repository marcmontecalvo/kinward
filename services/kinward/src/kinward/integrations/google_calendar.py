from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from kinward.integrations.oauth import OAuthExchangeError, OAuthTokens

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

# calendar.readonly is enough for Epic 5's v0/v1 read-only scope; openid+email
# identify which Google account was connected (shown back to the household, and
# used to detect "you already connected this same account").
SCOPES = ("openid", "email", "https://www.googleapis.com/auth/calendar.readonly")

# Google's attendee responseStatus vocabulary -> the canonical vocabulary
# domain/calendar_observation.py::rsvp_needs_response already understands.
_RSVP_MAP = {
    "needsAction": "needs_action",
    "tentative": "tentative",
    "accepted": "accepted",
    "declined": "declined",
}


def build_authorize_url(*, client_id: str, redirect_uri: str, state: str, code_challenge: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        # offline+consent guarantees a refresh_token even on a re-connect, not just
        # the account's very first authorization.
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(
    *, client_id: str, client_secret: str, redirect_uri: str, code: str, code_verifier: str
) -> OAuthTokens:
    return await _post_token(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
    )


async def refresh_tokens(*, client_id: str, client_secret: str, refresh_token: str) -> OAuthTokens:
    return await _post_token(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )


async def _post_token(data: dict[str, str]) -> OAuthTokens:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(TOKEN_URL, data=data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthExchangeError(str(exc)) from exc
    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str):
        raise OAuthExchangeError("Google token response missing access_token")
    return OAuthTokens(
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        expires_in=int(payload.get("expires_in", 3600)),
    )


async def fetch_account_email(access_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(USERINFO_URL, headers=_auth_headers(access_token))
            response.raise_for_status()
        except httpx.HTTPError:
            return None
    email = response.json().get("email")
    return email if isinstance(email, str) else None


async def list_events(access_token: str, *, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Fetch primary-calendar events in ``[start, end)``, normalized into the same raw
    shape ``domain/calendar_observation.py::observe_event`` already parses for Home
    Assistant's ``/api/calendars/{entity_id}`` rows - Google's own ``start``/``end``
    dict shape (``{"dateTime": ...}``/``{"date": ...}``) matches it natively, so the
    entire downstream detection/attention/briefing pipeline runs unchanged.

    Returns ``[]`` on any request failure - callers treat that the same as HA's
    ``calendar_events`` returning no events this pass, not a fatal error.
    """
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "250",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(EVENTS_URL, headers=_auth_headers(access_token), params=params)
            response.raise_for_status()
        except httpx.HTTPError:
            return []
    items = response.json().get("items")
    if not isinstance(items, list):
        return []
    return [_normalize_event(item) for item in items if isinstance(item, dict)]


async def revoke_token(token: str) -> None:
    """Best-effort revocation on disconnect - a failure here (already revoked,
    network hiccup) never blocks deleting the local row; the token still expires or
    the account owner can revoke it themselves from their Google account settings.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(REVOKE_URL, params={"token": token})
        except httpx.HTTPError:
            pass


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _normalize_event(item: dict[str, Any]) -> dict[str, Any]:
    rsvp_status = None
    attendees = item.get("attendees")
    if isinstance(attendees, list):
        for attendee in attendees:
            if isinstance(attendee, dict) and attendee.get("self"):
                rsvp_status = _RSVP_MAP.get(attendee.get("responseStatus", ""))
                break
    return {
        "uid": item.get("id"),
        "summary": item.get("summary") or "(untitled event)",
        "start": item.get("start"),
        "end": item.get("end"),
        "location": item.get("location"),
        "rsvp_status": rsvp_status,
    }
