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
class HaPerson:
    """One Home Assistant ``person.*`` entity, as read from ``hass.states.async_all``.

    ``is_admin`` reflects the linked HA user's current admin flag (false if there's
    no linked user at all) - Kinward has no admin designation of its own; whoever is
    an HA administrator is a Kinward administrator, and any number of people can hold
    that role at once.
    """

    ha_person_id: str
    ha_user_id: str | None
    display_name: str
    is_admin: bool = False


@dataclass(frozen=True)
class SyncedPerson:
    """A Kinward person as reported back by the sync endpoint."""

    id: str
    ha_person_id: str
    ha_user_id: str | None
    display_name: str
    role: str


@dataclass(frozen=True)
class SyncPeopleSuccess:
    people: list[SyncedPerson]


@dataclass(frozen=True)
class SyncPeopleFailure:
    error: ConfigFlowErrorCode


SyncPeopleResult = SyncPeopleSuccess | SyncPeopleFailure


@dataclass(frozen=True)
class Pet:
    """A household-shared pet profile, as reported by the pets endpoint."""

    id: str
    display_name: str
    species: str
    shared_facts: list[str]


@dataclass(frozen=True)
class PetsSuccess:
    pets: list[Pet]


@dataclass(frozen=True)
class PetsFailure:
    error: ConfigFlowErrorCode


PetsResult = PetsSuccess | PetsFailure


@dataclass(frozen=True)
class ProviderSettings:
    """The household's model/memory/knowledge connection settings.

    ``has_model_api_key`` reports whether a key is set without ever echoing the
    secret itself back - the options flow can only set or replace it, never see it.
    """

    model_provider: str
    model_base_url: str | None
    model_name: str | None
    has_model_api_key: bool
    memory_backend: str
    honcho_url: str | None
    knowledge_backend: str
    llm_wiki_url: str | None


@dataclass(frozen=True)
class ProviderSettingsFailure:
    error: ConfigFlowErrorCode


ProviderSettingsResult = ProviderSettings | ProviderSettingsFailure


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


def _synced_person_from(payload: Any) -> SyncedPerson | None:
    if not isinstance(payload, dict):
        return None
    person_id = payload.get("id")
    ha_person_id = payload.get("haPersonId")
    ha_user_id = payload.get("haUserId")
    display_name = payload.get("displayName")
    role = payload.get("role")
    if (
        not isinstance(person_id, str)
        or not isinstance(ha_person_id, str)
        or not isinstance(display_name, str)
        or not isinstance(role, str)
    ):
        return None
    if ha_user_id is not None and not isinstance(ha_user_id, str):
        return None
    return SyncedPerson(
        id=person_id, ha_person_id=ha_person_id, ha_user_id=ha_user_id, display_name=display_name, role=role
    )


def classify_sync_people_response(status_code: int, payload: Any) -> SyncPeopleResult:
    if status_code == 401:
        return SyncPeopleFailure("invalid_auth")
    if status_code == 409:
        return SyncPeopleFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return SyncPeopleFailure("unknown")
    people: list[SyncedPerson] = []
    for item in payload:
        person = _synced_person_from(item)
        if person is None:
            return SyncPeopleFailure("unknown")
        people.append(person)
    return SyncPeopleSuccess(people=people)


def _pet_from(payload: Any) -> Pet | None:
    if not isinstance(payload, dict):
        return None
    pet_id = payload.get("id")
    display_name = payload.get("displayName")
    species = payload.get("species")
    shared_facts = payload.get("sharedFacts")
    if (
        not isinstance(pet_id, str)
        or not isinstance(display_name, str)
        or not isinstance(species, str)
        or not isinstance(shared_facts, list)
        or not all(isinstance(fact, str) for fact in shared_facts)
    ):
        return None
    return Pet(id=pet_id, display_name=display_name, species=species, shared_facts=shared_facts)


def classify_pets_response(status_code: int, payload: Any) -> PetsResult:
    if status_code == 401:
        return PetsFailure("invalid_auth")
    if status_code == 409:
        return PetsFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return PetsFailure("unknown")
    pets: list[Pet] = []
    for item in payload:
        pet = _pet_from(item)
        if pet is None:
            return PetsFailure("unknown")
        pets.append(pet)
    return PetsSuccess(pets=pets)


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


def _provider_settings_from(payload: Any) -> ProviderSettings | None:
    if not isinstance(payload, dict):
        return None
    model_provider = payload.get("modelProvider")
    memory_backend = payload.get("memoryBackend")
    knowledge_backend = payload.get("knowledgeBackend")
    has_model_api_key = payload.get("hasModelApiKey")
    if (
        not isinstance(model_provider, str)
        or not isinstance(memory_backend, str)
        or not isinstance(knowledge_backend, str)
        or not isinstance(has_model_api_key, bool)
    ):
        return None
    model_base_url = payload.get("modelBaseUrl")
    model_name = payload.get("modelName")
    honcho_url = payload.get("honchoUrl")
    llm_wiki_url = payload.get("llmWikiUrl")
    for value in (model_base_url, model_name, honcho_url, llm_wiki_url):
        if value is not None and not isinstance(value, str):
            return None
    return ProviderSettings(
        model_provider=model_provider,
        model_base_url=model_base_url,
        model_name=model_name,
        has_model_api_key=has_model_api_key,
        memory_backend=memory_backend,
        honcho_url=honcho_url,
        knowledge_backend=knowledge_backend,
        llm_wiki_url=llm_wiki_url,
    )


def classify_provider_settings_response(status_code: int, payload: Any) -> ProviderSettingsResult:
    if status_code == 401:
        return ProviderSettingsFailure("invalid_auth")
    if status_code == 409:
        return ProviderSettingsFailure("household_not_configured")
    if status_code != 200:
        return ProviderSettingsFailure("unknown")
    settings = _provider_settings_from(payload)
    if settings is None:
        return ProviderSettingsFailure("unknown")
    return settings


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

    async def async_sync_people(self, people: list[HaPerson]) -> SyncPeopleResult:
        body = [
            {
                "haPersonId": person.ha_person_id,
                "haUserId": person.ha_user_id,
                "displayName": person.display_name,
                "isAdmin": person.is_admin,
            }
            for person in people
        ]
        try:
            status, payload = await self._request(
                "PUT", "/api/v1/integration/people/sync", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return SyncPeopleFailure("cannot_connect")
        return classify_sync_people_response(status, payload)

    async def async_fetch_pets(self) -> PetsResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/pets")
        except (TimeoutError, aiohttp.ClientError):
            return PetsFailure("cannot_connect")
        return classify_pets_response(status, payload)

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

    async def async_fetch_provider_settings(self) -> ProviderSettingsResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/settings/providers")
        except (TimeoutError, aiohttp.ClientError):
            return ProviderSettingsFailure("cannot_connect")
        return classify_provider_settings_response(status, payload)

    async def async_update_provider_settings(
        self,
        *,
        model_provider: str,
        model_base_url: str,
        model_name: str,
        model_api_key: str | None,
        memory_backend: str,
        honcho_url: str,
        knowledge_backend: str,
        llm_wiki_url: str,
    ) -> ProviderSettingsResult:
        """``model_api_key`` is omitted from the request entirely when blank - the settings
        screen can never show the current key back to prefill it, so a blank submission
        must mean "leave it as-is", never "clear it".
        """
        body: dict[str, Any] = {
            "modelProvider": model_provider,
            "modelBaseUrl": model_base_url,
            "modelName": model_name,
            "memoryBackend": memory_backend,
            "honchoUrl": honcho_url,
            "knowledgeBackend": knowledge_backend,
            "llmWikiUrl": llm_wiki_url,
        }
        if model_api_key:
            body["modelApiKey"] = model_api_key
        try:
            status, payload = await self._request(
                "PATCH", "/api/v1/integration/settings/providers", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return ProviderSettingsFailure("cannot_connect")
        return classify_provider_settings_response(status, payload)
