from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from kinward.integrations.oauth import OAuthExchangeError, OAuthTokens

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"
GRAPH_CALENDARVIEW_URL = "https://graph.microsoft.com/v1.0/me/calendarview"

# offline_access is required for a refresh_token; Calendars.Read/User.Read are the
# minimum read-only Epic 5 scope needs.
SCOPES = ("offline_access", "User.Read", "Calendars.Read")

# Microsoft Graph's attendee response vocabulary -> the canonical vocabulary
# domain/calendar_observation.py::rsvp_needs_response already understands.
# "organizer" needs no response of its own; "none"/"notResponded" both mean
# "hasn't answered yet."
_RSVP_MAP = {
    "none": "needs_action",
    "notResponded": "needs_action",
    "organizer": "accepted",
    "tentativelyAccepted": "tentative",
    "accepted": "accepted",
    "declined": "declined",
}


def _authorize_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"


def _token_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def build_authorize_url(
    *, tenant: str, client_id: str, redirect_uri: str, state: str, code_challenge: str
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{_authorize_url(tenant)}?{urlencode(params)}"


async def exchange_code(
    *,
    tenant: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    code_verifier: str,
) -> OAuthTokens:
    return await _post_token(
        tenant,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "scope": " ".join(SCOPES),
        },
    )


async def refresh_tokens(
    *, tenant: str, client_id: str, client_secret: str, refresh_token: str
) -> OAuthTokens:
    return await _post_token(
        tenant,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(SCOPES),
        },
    )


async def _post_token(tenant: str, data: dict[str, str]) -> OAuthTokens:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(_token_url(tenant), data=data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthExchangeError(str(exc)) from exc
    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str):
        raise OAuthExchangeError("Microsoft token response missing access_token")
    return OAuthTokens(
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        expires_in=int(payload.get("expires_in", 3600)),
    )


async def fetch_account_email(access_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(GRAPH_ME_URL, headers=_auth_headers(access_token))
            response.raise_for_status()
        except httpx.HTTPError:
            return None
    payload = response.json()
    email = payload.get("mail") or payload.get("userPrincipalName")
    return email if isinstance(email, str) else None


async def list_events(access_token: str, *, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Fetch calendar events in ``[start, end)`` via Graph's ``calendarview``,
    normalized into the same raw shape ``domain/calendar_observation.py::observe_event``
    already parses for Home Assistant's ``/api/calendars/{entity_id}`` rows.

    ``Prefer: outlook.timezone="UTC"`` makes Graph return every ``dateTime`` already
    in UTC (Graph otherwise returns each event's own local time with no offset,
    unusable without a Windows-timezone lookup table) - ``_normalize_event`` then only
    has to append the missing ``Z``, matching Google/HA's ISO-8601 shape exactly.

    Returns ``[]`` on any request failure - callers treat that the same as HA's
    ``calendar_events`` returning no events this pass, not a fatal error.
    """
    params = {"startDateTime": start.isoformat(), "endDateTime": end.isoformat(), "$top": "250"}
    headers = {**_auth_headers(access_token), "Prefer": 'outlook.timezone="UTC"'}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(GRAPH_CALENDARVIEW_URL, headers=headers, params=params)
            response.raise_for_status()
        except httpx.HTTPError:
            return []
    items = response.json().get("value")
    if not isinstance(items, list):
        return []
    return [_normalize_event(item) for item in items if isinstance(item, dict)]


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _normalize_datetime(raw: dict[str, Any]) -> dict[str, Any] | None:
    value = raw.get("dateTime")
    if not isinstance(value, str):
        return None
    if "." in value:
        base, _, frac = value.partition(".")
        value = f"{base}.{frac[:6].ljust(6, '0')}"
    return {"dateTime": f"{value}Z"}


def _normalize_event(item: dict[str, Any]) -> dict[str, Any]:
    is_all_day = bool(item.get("isAllDay"))
    raw_start_value = item.get("start")
    raw_end_value = item.get("end")
    raw_start: dict[str, Any] = raw_start_value if isinstance(raw_start_value, dict) else {}
    raw_end: dict[str, Any] = raw_end_value if isinstance(raw_end_value, dict) else {}

    if is_all_day:
        start_date = raw_start.get("dateTime")
        end_date = raw_end.get("dateTime")
        start = {"date": start_date[:10]} if isinstance(start_date, str) else None
        end = {"date": end_date[:10]} if isinstance(end_date, str) else None
    else:
        start = _normalize_datetime(raw_start)
        end = _normalize_datetime(raw_end)

    response_status = item.get("responseStatus")
    rsvp_status = None
    if isinstance(response_status, dict):
        rsvp_status = _RSVP_MAP.get(response_status.get("response", ""))

    location = item.get("location")
    location_name = location.get("displayName") if isinstance(location, dict) else None

    return {
        "uid": item.get("iCalUId") or item.get("id"),
        "summary": item.get("subject") or "(untitled event)",
        "start": start,
        "end": end,
        "location": location_name,
        "rsvp_status": rsvp_status,
    }
