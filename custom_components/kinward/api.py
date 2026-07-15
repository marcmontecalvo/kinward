"""Typed, minimal-dependency client for the Kinward backend's /api/v1/integration contract.

Response classification is kept in pure functions with no ``homeassistant.*`` or
``aiohttp`` imports so they can be unit-tested without a Home Assistant test harness.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal

import aiohttp

from .const import CONTRACT_VERSION, REQUEST_TIMEOUT_SECONDS

ConfigFlowErrorCode = Literal[
    "cannot_connect",
    "invalid_auth",
    "incompatible_api",
    "household_not_configured",
    "unknown",
]


@dataclass(frozen=True)
class ContextSuccess:
    household_id: str
    household_name: str
    contract_version: str


@dataclass(frozen=True)
class ContextFailure:
    error: ConfigFlowErrorCode


ContextResult = ContextSuccess | ContextFailure


@dataclass(frozen=True)
class CapabilityStatus:
    state: str
    reason: str | None = None


@dataclass(frozen=True)
class BriefingStatus(CapabilityStatus):
    summary: str | None = None


@dataclass(frozen=True)
class AttentionStatus(CapabilityStatus):
    count: int | None = None


@dataclass(frozen=True)
class NextEventStatus(CapabilityStatus):
    summary: str | None = None
    starts_at: str | None = None


@dataclass(frozen=True)
class SummarySuccess:
    adult_count: int
    child_count: int
    briefing: BriefingStatus
    attention: AttentionStatus
    next_event: NextEventStatus


@dataclass(frozen=True)
class SummaryFailure:
    error: ConfigFlowErrorCode


SummaryResult = SummarySuccess | SummaryFailure


@dataclass(frozen=True)
class Person:
    id: str
    display_name: str


@dataclass(frozen=True)
class PeopleSuccess:
    people: list[Person]


@dataclass(frozen=True)
class PeopleFailure:
    error: ConfigFlowErrorCode


PeopleResult = PeopleSuccess | PeopleFailure


@dataclass(frozen=True)
class SendMessageSuccess:
    conversation_id: str | None
    outcome: str
    response_text: str
    mapped: bool


@dataclass(frozen=True)
class SendMessageFailure:
    error: ConfigFlowErrorCode


SendMessageResult = SendMessageSuccess | SendMessageFailure


@dataclass(frozen=True)
class HaUserMapping:
    ha_user_id: str
    person_id: str


@dataclass(frozen=True)
class MappingsSuccess:
    mappings: list[HaUserMapping]


@dataclass(frozen=True)
class MappingsFailure:
    error: ConfigFlowErrorCode


MappingsResult = MappingsSuccess | MappingsFailure


def classify_context_response(status_code: int, payload: Any) -> ContextResult:
    if status_code == 200 and isinstance(payload, dict):
        household_id = payload.get("householdId")
        household_name = payload.get("householdName")
        contract_version = payload.get("contractVersion")
        if not isinstance(household_id, str) or not isinstance(household_name, str):
            return ContextFailure("unknown")
        if contract_version != CONTRACT_VERSION:
            return ContextFailure("incompatible_api")
        return ContextSuccess(household_id, household_name, str(contract_version))
    if status_code == 401:
        return ContextFailure("invalid_auth")
    if status_code == 409:
        return ContextFailure("household_not_configured")
    return ContextFailure("unknown")


def _capability(payload: Any) -> CapabilityStatus:
    if not isinstance(payload, dict):
        return CapabilityStatus(state="unavailable", reason="malformed-response")
    state = payload.get("state")
    reason = payload.get("reason")
    return CapabilityStatus(
        state=state if isinstance(state, str) else "unavailable",
        reason=reason if isinstance(reason, str) else None,
    )


def classify_summary_response(status_code: int, payload: Any) -> SummaryResult:
    if status_code == 401:
        return SummaryFailure("invalid_auth")
    if status_code == 409:
        return SummaryFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, dict):
        return SummaryFailure("unknown")

    household = payload.get("household")
    if not isinstance(household, dict):
        return SummaryFailure("unknown")
    adult_count = household.get("adultCount")
    child_count = household.get("childCount")
    if not isinstance(adult_count, int) or not isinstance(child_count, int):
        return SummaryFailure("unknown")

    briefing_raw = payload.get("briefing") or {}
    attention_raw = payload.get("attention") or {}
    next_event_raw = payload.get("nextEvent") or {}
    base_briefing = _capability(briefing_raw)
    base_attention = _capability(attention_raw)
    base_next_event = _capability(next_event_raw)

    return SummarySuccess(
        adult_count=adult_count,
        child_count=child_count,
        briefing=BriefingStatus(
            state=base_briefing.state,
            reason=base_briefing.reason,
            summary=briefing_raw.get("summary") if isinstance(briefing_raw, dict) else None,
        ),
        attention=AttentionStatus(
            state=base_attention.state,
            reason=base_attention.reason,
            count=attention_raw.get("count") if isinstance(attention_raw, dict) else None,
        ),
        next_event=NextEventStatus(
            state=base_next_event.state,
            reason=base_next_event.reason,
            summary=next_event_raw.get("summary") if isinstance(next_event_raw, dict) else None,
            starts_at=next_event_raw.get("startsAt") if isinstance(next_event_raw, dict) else None,
        ),
    )


def classify_people_response(status_code: int, payload: Any) -> PeopleResult:
    if status_code == 401:
        return PeopleFailure("invalid_auth")
    if status_code == 409:
        return PeopleFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return PeopleFailure("unknown")
    people: list[Person] = []
    for item in payload:
        if not isinstance(item, dict):
            return PeopleFailure("unknown")
        person_id = item.get("id")
        display_name = item.get("displayName")
        if not isinstance(person_id, str) or not isinstance(display_name, str):
            return PeopleFailure("unknown")
        people.append(Person(id=person_id, display_name=display_name))
    return PeopleSuccess(people=people)


def classify_mappings_response(status_code: int, payload: Any) -> MappingsResult:
    if status_code == 401:
        return MappingsFailure("invalid_auth")
    if status_code == 409:
        return MappingsFailure("household_not_configured")
    if status_code == 422:
        return MappingsFailure("unknown")
    if status_code != 200 or not isinstance(payload, list):
        return MappingsFailure("unknown")
    mappings: list[HaUserMapping] = []
    for item in payload:
        if not isinstance(item, dict):
            return MappingsFailure("unknown")
        ha_user_id = item.get("haUserId")
        person_id = item.get("personId")
        if not isinstance(ha_user_id, str) or not isinstance(person_id, str):
            return MappingsFailure("unknown")
        mappings.append(HaUserMapping(ha_user_id=ha_user_id, person_id=person_id))
    return MappingsSuccess(mappings=mappings)


def classify_send_message_response(status_code: int, payload: Any) -> SendMessageResult:
    if status_code == 401:
        return SendMessageFailure("invalid_auth")
    if status_code == 409:
        return SendMessageFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, dict):
        return SendMessageFailure("unknown")

    conversation_id = payload.get("conversationId")
    outcome = payload.get("outcome")
    response_text = payload.get("responseText")
    mapped = payload.get("mapped")
    if not isinstance(outcome, str) or not isinstance(response_text, str) or not isinstance(mapped, bool):
        return SendMessageFailure("unknown")
    if conversation_id is not None and not isinstance(conversation_id, str):
        return SendMessageFailure("unknown")
    return SendMessageSuccess(
        conversation_id=conversation_id, outcome=outcome, response_text=response_text, mapped=mapped
    )


class KinwardApiClient:
    """Thin async wrapper; all response interpretation lives in the pure classify_* functions."""

    def __init__(self, session: aiohttp.ClientSession, *, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def _request(self, method: str, path: str, *, json_body: Any = None) -> tuple[int, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
            async with self._session.request(
                method, f"{self._base_url}{path}", headers=headers, json=json_body
            ) as response:
                status = response.status
                try:
                    payload = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    payload = None
        return status, payload

    async def async_fetch_context(self) -> ContextResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/context")
        except (TimeoutError, aiohttp.ClientError):
            return ContextFailure("cannot_connect")
        return classify_context_response(status, payload)

    async def async_fetch_summary(self) -> SummaryResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/summary")
        except (TimeoutError, aiohttp.ClientError):
            return SummaryFailure("cannot_connect")
        return classify_summary_response(status, payload)

    async def async_fetch_people(self) -> PeopleResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/people")
        except (TimeoutError, aiohttp.ClientError):
            return PeopleFailure("cannot_connect")
        return classify_people_response(status, payload)

    async def async_fetch_ha_user_mappings(self) -> MappingsResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/ha-user-mappings")
        except (TimeoutError, aiohttp.ClientError):
            return MappingsFailure("cannot_connect")
        return classify_mappings_response(status, payload)

    async def async_put_ha_user_mappings(
        self, mappings: list[HaUserMapping]
    ) -> MappingsResult:
        body = [{"haUserId": item.ha_user_id, "personId": item.person_id} for item in mappings]
        try:
            status, payload = await self._request(
                "PUT", "/api/v1/integration/ha-user-mappings", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return MappingsFailure("cannot_connect")
        return classify_mappings_response(status, payload)

    async def async_send_conversation_message(
        self, *, ha_user_id: str, text: str, conversation_id: str | None, language: str
    ) -> SendMessageResult:
        body = {
            "haUserId": ha_user_id,
            "text": text,
            "conversationId": conversation_id,
            "language": language,
        }
        try:
            status, payload = await self._request(
                "POST", "/api/v1/integration/conversation", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return SendMessageFailure("cannot_connect")
        return classify_send_message_response(status, payload)

    async def async_delete_ha_user_mapping(self, ha_user_id: str) -> bool:
        try:
            status, _payload = await self._request(
                "DELETE", f"/api/v1/integration/ha-user-mappings/{ha_user_id}"
            )
        except (TimeoutError, aiohttp.ClientError):
            return False
        return status == 204
