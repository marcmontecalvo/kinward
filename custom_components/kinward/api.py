"""Typed, minimal-dependency client for the Kinward backend's /api/v1/integration contract.

Response classification is kept in pure functions with no ``homeassistant.*`` or
``aiohttp`` imports so they can be unit-tested without a Home Assistant test harness.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import quote

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
class Person:
    """A synced household person, as reported by the people endpoint - just enough

    to resolve a display name to the internal id ADR-002's allowlist needs.
    """

    id: str
    display_name: str


@dataclass(frozen=True)
class PeopleFailure:
    error: ConfigFlowErrorCode


PeopleResult = list[Person] | PeopleFailure


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


@dataclass(frozen=True)
class AssistantPolicy:
    max_assistants_per_person: int | None
    require_admin_approval_for_creation: bool


@dataclass(frozen=True)
class AssistantPolicyFailure:
    error: ConfigFlowErrorCode


AssistantPolicyResult = AssistantPolicy | AssistantPolicyFailure


@dataclass(frozen=True)
class ToolPolicy:
    """Per-capability HA write permission (Epic 7 Story 7.3): ``allow`` /

    ``approval_required`` / ``deny``, keyed by capability name (e.g.
    ``control_lights``, ``control_locks``).
    """

    permissions: dict[str, str]


@dataclass(frozen=True)
class ToolPolicyFailure:
    error: ConfigFlowErrorCode


ToolPolicyResult = ToolPolicy | ToolPolicyFailure


@dataclass(frozen=True)
class ResourceLabel:
    """One admin-set household-language label override for an HA entity id (Story 7.1)."""

    entity_id: str
    label: str
    record_version: int


@dataclass(frozen=True)
class ResourceLabelFailure:
    error: ConfigFlowErrorCode


ResourceLabelResult = ResourceLabel | ResourceLabelFailure
ResourceLabelsResult = list[ResourceLabel] | ResourceLabelFailure


@dataclass(frozen=True)
class Assistant:
    id: str
    name: str
    personality: dict[str, Any]
    access_mode: str
    allowed_person_ids: list[str]
    visual_pack_id: str
    interview_state: str
    visual_stage: str


@dataclass(frozen=True)
class AssistantActionFailure:
    """A named, human-readable reason a create/list/delete action didn't happen -

    a policy rejection (e.g. "max_assistants_reached"), a not-found, or a transport
    failure ("cannot_connect"). There's no form to route this into like the config/
    options flow errors - the create/delete services just log it.
    """

    reason: str


def _assistant_from(payload: Any) -> Assistant | None:
    if not isinstance(payload, dict):
        return None
    assistant_id = payload.get("id")
    name = payload.get("name")
    personality = payload.get("personality")
    access_mode = payload.get("accessMode")
    allowed_person_ids = payload.get("allowedPersonIds")
    visual_pack_id = payload.get("visualPackId")
    interview_state = payload.get("interviewState")
    visual_stage = payload.get("visualStage")
    if (
        not isinstance(assistant_id, str)
        or not isinstance(name, str)
        or not isinstance(personality, dict)
        or not isinstance(access_mode, str)
        or not isinstance(allowed_person_ids, list)
        or not all(isinstance(item, str) for item in allowed_person_ids)
        or not isinstance(visual_pack_id, str)
        or not isinstance(interview_state, str)
        or not isinstance(visual_stage, str)
    ):
        return None
    return Assistant(
        id=assistant_id,
        name=name,
        personality=personality,
        access_mode=access_mode,
        allowed_person_ids=allowed_person_ids,
        visual_pack_id=visual_pack_id,
        interview_state=interview_state,
        visual_stage=visual_stage,
    )


@dataclass(frozen=True)
class AssistantIdentity:
    """The public-only subset of an assistant's fields (Epic 3 Story 3.7) - never

    ``personality``. Safe for household-wide display (e.g. a shared sensor or the
    Story 10.5 Lovelace card) because it carries nothing private, unlike ``Assistant``
    above which is always fetched scoped to one person's own ``ha_user_id``.
    """

    id: str
    name: str
    owner_person_id: str | None
    visual_pack_id: str
    visual_stage: str
    visual_stage_icon: str
    visual_stage_preview_image: str | None
    accent: str


@dataclass(frozen=True)
class AssistantIdentitiesFailure:
    error: str


def _assistant_identity_from(payload: Any) -> AssistantIdentity | None:
    if not isinstance(payload, dict):
        return None
    assistant_id = payload.get("id")
    name = payload.get("name")
    owner_person_id = payload.get("ownerPersonId")
    visual_pack_id = payload.get("visualPackId")
    visual_stage = payload.get("visualStage")
    visual_stage_icon = payload.get("visualStageIcon")
    visual_stage_preview_image = payload.get("visualStagePreviewImage")
    accent = payload.get("accent")
    if (
        not isinstance(assistant_id, str)
        or not isinstance(name, str)
        or not (owner_person_id is None or isinstance(owner_person_id, str))
        or not isinstance(visual_pack_id, str)
        or not isinstance(visual_stage, str)
        or not isinstance(visual_stage_icon, str)
        or not (visual_stage_preview_image is None or isinstance(visual_stage_preview_image, str))
        or not isinstance(accent, str)
    ):
        return None
    return AssistantIdentity(
        id=assistant_id,
        name=name,
        owner_person_id=owner_person_id,
        visual_pack_id=visual_pack_id,
        visual_stage=visual_stage,
        visual_stage_icon=visual_stage_icon,
        visual_stage_preview_image=visual_stage_preview_image,
        accent=accent,
    )


def classify_assistant_identities_response(
    status_code: int, payload: Any
) -> list[AssistantIdentity] | AssistantIdentitiesFailure:
    if status_code != 200 or not isinstance(payload, list):
        return AssistantIdentitiesFailure(error=_error_reason(status_code, payload))
    return [identity for item in payload if (identity := _assistant_identity_from(item)) is not None]


@dataclass(frozen=True)
class VisualPackStage:
    name: str
    mdi_icon: str
    preview_image: str | None


@dataclass(frozen=True)
class VisualPack:
    id: str
    display_name: str
    category: str
    default_accent: str
    stages: list[VisualPackStage]


@dataclass(frozen=True)
class VisualPacksFailure:
    error: str


def _visual_pack_from(payload: Any) -> VisualPack | None:
    if not isinstance(payload, dict):
        return None
    stages_raw = payload.get("stages")
    if not isinstance(stages_raw, list):
        return None
    stages: list[VisualPackStage] = []
    for stage in stages_raw:
        if not isinstance(stage, dict):
            return None
        name, mdi_icon = stage.get("name"), stage.get("mdiIcon")
        if not isinstance(name, str) or not isinstance(mdi_icon, str):
            return None
        preview_image = stage.get("previewImage")
        stages.append(
            VisualPackStage(
                name=name,
                mdi_icon=mdi_icon,
                preview_image=preview_image if isinstance(preview_image, str) else None,
            )
        )
    pack_id, display_name = payload.get("id"), payload.get("displayName")
    category, default_accent = payload.get("category"), payload.get("defaultAccent")
    if (
        not isinstance(pack_id, str)
        or not isinstance(display_name, str)
        or not isinstance(category, str)
        or not isinstance(default_accent, str)
    ):
        return None
    return VisualPack(
        id=pack_id, display_name=display_name, category=category, default_accent=default_accent, stages=stages
    )


def classify_visual_packs_response(status_code: int, payload: Any) -> list[VisualPack] | VisualPacksFailure:
    if status_code != 200 or not isinstance(payload, list):
        return VisualPacksFailure(error=_error_reason(status_code, payload))
    return [pack for item in payload if (pack := _visual_pack_from(item)) is not None]


@dataclass(frozen=True)
class PersonaImportProposal:
    dimensions: dict[str, str]
    grounding_notes: str


@dataclass(frozen=True)
class PersonaImportFailure:
    error: str


def classify_persona_import_response(
    status_code: int, payload: Any
) -> PersonaImportProposal | PersonaImportFailure:
    if status_code != 200 or not isinstance(payload, dict):
        return PersonaImportFailure(error=_error_reason(status_code, payload))
    dimensions = payload.get("dimensions")
    grounding_notes = payload.get("groundingNotes")
    if not isinstance(dimensions, dict) or not isinstance(grounding_notes, str):
        return PersonaImportFailure(error="malformed response")
    return PersonaImportProposal(
        dimensions={k: v for k, v in dimensions.items() if isinstance(v, str)},
        grounding_notes=grounding_notes,
    )


def _error_reason(status_code: int, payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str):
                return message
            code = detail.get("code")
            if isinstance(code, str):
                return code
    return f"unexpected status {status_code}"


def classify_assistant_policy_response(status_code: int, payload: Any) -> AssistantPolicyResult:
    if status_code == 401:
        return AssistantPolicyFailure("invalid_auth")
    if status_code == 409:
        return AssistantPolicyFailure("household_not_configured")
    if status_code != 200:
        return AssistantPolicyFailure("unknown")
    if not isinstance(payload, dict):
        return AssistantPolicyFailure("unknown")
    max_assistants = payload.get("maxAssistantsPerPerson")
    require_approval = payload.get("requireAdminApprovalForCreation")
    if max_assistants is not None and not isinstance(max_assistants, int):
        return AssistantPolicyFailure("unknown")
    if not isinstance(require_approval, bool):
        return AssistantPolicyFailure("unknown")
    return AssistantPolicy(
        max_assistants_per_person=max_assistants,
        require_admin_approval_for_creation=require_approval,
    )


def classify_tool_policy_response(status_code: int, payload: Any) -> ToolPolicyResult:
    if status_code == 401:
        return ToolPolicyFailure("invalid_auth")
    if status_code == 409:
        return ToolPolicyFailure("household_not_configured")
    if status_code != 200:
        return ToolPolicyFailure("unknown")
    if not isinstance(payload, dict):
        return ToolPolicyFailure("unknown")
    permissions = payload.get("permissions")
    if not isinstance(permissions, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in permissions.items()
    ):
        return ToolPolicyFailure("unknown")
    return ToolPolicy(permissions=dict(permissions))


def _resource_label_from(payload: Any) -> ResourceLabel | None:
    if not isinstance(payload, dict):
        return None
    entity_id = payload.get("entityId")
    label = payload.get("label")
    record_version = payload.get("recordVersion")
    if (
        not isinstance(entity_id, str)
        or not isinstance(label, str)
        or not isinstance(record_version, int)
    ):
        return None
    return ResourceLabel(entity_id=entity_id, label=label, record_version=record_version)


def classify_resource_labels_response(status_code: int, payload: Any) -> ResourceLabelsResult:
    if status_code == 401:
        return ResourceLabelFailure("invalid_auth")
    if status_code == 409:
        return ResourceLabelFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return ResourceLabelFailure("unknown")
    labels: list[ResourceLabel] = []
    for item in payload:
        label = _resource_label_from(item)
        if label is None:
            return ResourceLabelFailure("unknown")
        labels.append(label)
    return labels


def classify_resource_label_response(status_code: int, payload: Any) -> ResourceLabelResult:
    if status_code == 401:
        return ResourceLabelFailure("invalid_auth")
    if status_code == 409:
        return ResourceLabelFailure("household_not_configured")
    if status_code != 200:
        return ResourceLabelFailure("unknown")
    label = _resource_label_from(payload)
    if label is None:
        return ResourceLabelFailure("unknown")
    return label


def classify_list_assistants_response(
    status_code: int, payload: Any
) -> list[Assistant] | AssistantActionFailure:
    if status_code != 200 or not isinstance(payload, list):
        return AssistantActionFailure(reason=_error_reason(status_code, payload))
    assistants = [assistant for item in payload if (assistant := _assistant_from(item)) is not None]
    return assistants


def classify_assistant_action_response(
    status_code: int, payload: Any
) -> Assistant | AssistantActionFailure:
    if status_code not in (200, 201):
        return AssistantActionFailure(reason=_error_reason(status_code, payload))
    assistant = _assistant_from(payload)
    if assistant is None:
        return AssistantActionFailure(reason="malformed response")
    return assistant


def classify_delete_assistant_response(status_code: int, payload: Any) -> AssistantActionFailure | None:
    if status_code == 204:
        return None
    return AssistantActionFailure(reason=_error_reason(status_code, payload))


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


def _person_from(payload: Any) -> Person | None:
    if not isinstance(payload, dict):
        return None
    person_id = payload.get("id")
    display_name = payload.get("displayName")
    if not isinstance(person_id, str) or not isinstance(display_name, str):
        return None
    return Person(id=person_id, display_name=display_name)


def classify_people_response(status_code: int, payload: Any) -> PeopleResult:
    if status_code == 401:
        return PeopleFailure("invalid_auth")
    if status_code == 409:
        return PeopleFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return PeopleFailure("unknown")
    people: list[Person] = []
    for item in payload:
        person = _person_from(item)
        if person is None:
            return PeopleFailure("unknown")
        people.append(person)
    return people


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


@dataclass(frozen=True)
class PendingAction:
    """A currently-pending meaningful action awaiting admin approval (Epic 6; ADR-002 sec. 5)."""

    id: str
    requested_by_person_id: str
    action: str
    explanation: str
    domain: str
    service: str
    entity_id: str
    created_at: str
    expires_at: str | None


@dataclass(frozen=True)
class PendingActionsFailure:
    error: ConfigFlowErrorCode


PendingActionsResult = list[PendingAction] | PendingActionsFailure


@dataclass(frozen=True)
class ActionResult:
    """The outcome of requesting or resolving an action: ``executed``, ``denied``,
    ``pending_approval``, or ``failed`` - see ``application.pending_actions`` for
    what each means.
    """

    outcome: str
    approval_id: str | None = None


@dataclass(frozen=True)
class ActionFailure:
    reason: str


ActionOutcomeResult = ActionResult | ActionFailure


def _pending_action_from(payload: Any) -> PendingAction | None:
    if not isinstance(payload, dict):
        return None
    action_id = payload.get("id")
    requested_by_person_id = payload.get("requestedByPersonId")
    action = payload.get("action")
    explanation = payload.get("explanation")
    domain = payload.get("domain")
    service = payload.get("service")
    entity_id = payload.get("entityId")
    created_at = payload.get("createdAt")
    expires_at = payload.get("expiresAt")
    if (
        not isinstance(action_id, str)
        or not isinstance(requested_by_person_id, str)
        or not isinstance(action, str)
        or not isinstance(explanation, str)
        or not isinstance(domain, str)
        or not isinstance(service, str)
        or not isinstance(entity_id, str)
        or not isinstance(created_at, str)
    ):
        return None
    if expires_at is not None and not isinstance(expires_at, str):
        return None
    return PendingAction(
        id=action_id,
        requested_by_person_id=requested_by_person_id,
        action=action,
        explanation=explanation,
        domain=domain,
        service=service,
        entity_id=entity_id,
        created_at=created_at,
        expires_at=expires_at,
    )


def classify_pending_actions_response(status_code: int, payload: Any) -> PendingActionsResult:
    if status_code == 401:
        return PendingActionsFailure("invalid_auth")
    if status_code == 409:
        return PendingActionsFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return PendingActionsFailure("unknown")
    actions: list[PendingAction] = []
    for item in payload:
        action = _pending_action_from(item)
        if action is None:
            return PendingActionsFailure("unknown")
        actions.append(action)
    return actions


def classify_action_result_response(status_code: int, payload: Any) -> ActionOutcomeResult:
    if status_code != 200 or not isinstance(payload, dict):
        return ActionFailure(reason=_error_reason(status_code, payload))
    outcome = payload.get("outcome")
    if not isinstance(outcome, str):
        return ActionFailure(reason="malformed response")
    approval_id = payload.get("approvalId")
    if approval_id is not None and not isinstance(approval_id, str):
        return ActionFailure(reason="malformed response")
    return ActionResult(outcome=outcome, approval_id=approval_id)


@dataclass(frozen=True)
class CalendarEntity:
    """One HA ``calendar.*`` entity Kinward knows about (Epic 5 Story 5.1)."""

    entity_id: str
    enabled: bool
    known_to_ha: bool


@dataclass(frozen=True)
class CalendarEntitiesFailure:
    error: ConfigFlowErrorCode


CalendarEntitiesResult = list[CalendarEntity] | CalendarEntitiesFailure


def _calendar_entity_from(payload: Any) -> CalendarEntity | None:
    if not isinstance(payload, dict):
        return None
    entity_id = payload.get("entityId")
    enabled = payload.get("enabled")
    known_to_ha = payload.get("knownToHa")
    if not isinstance(entity_id, str) or not isinstance(enabled, bool) or not isinstance(known_to_ha, bool):
        return None
    return CalendarEntity(entity_id=entity_id, enabled=enabled, known_to_ha=known_to_ha)


def classify_calendar_entities_response(status_code: int, payload: Any) -> CalendarEntitiesResult:
    if status_code == 401:
        return CalendarEntitiesFailure("invalid_auth")
    if status_code == 409:
        return CalendarEntitiesFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return CalendarEntitiesFailure("unknown")
    entities: list[CalendarEntity] = []
    for item in payload:
        entity = _calendar_entity_from(item)
        if entity is None:
            return CalendarEntitiesFailure("unknown")
        entities.append(entity)
    return entities


def classify_set_calendar_entity_response(status_code: int, payload: Any) -> CalendarEntity | ActionFailure:
    if status_code != 200:
        return ActionFailure(reason=_error_reason(status_code, payload))
    entity = _calendar_entity_from(payload)
    if entity is None:
        return ActionFailure(reason="malformed response")
    return entity


@dataclass(frozen=True)
class AttentionItem:
    """One calendar attention item (Epic 5 Story 5.3): a durable record that a
    meaningful calendar condition may need notice or action.
    """

    id: str
    change_type: str
    state: str
    summary: str
    entity_id: str
    event_starts_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AttentionItemsFailure:
    error: ConfigFlowErrorCode


AttentionItemsResult = list[AttentionItem] | AttentionItemsFailure


def _attention_item_from(payload: Any) -> AttentionItem | None:
    if not isinstance(payload, dict):
        return None
    item_id = payload.get("id")
    change_type = payload.get("changeType")
    state = payload.get("state")
    summary = payload.get("summary")
    entity_id = payload.get("entityId")
    created_at = payload.get("createdAt")
    updated_at = payload.get("updatedAt")
    event_starts_at = payload.get("eventStartsAt")
    if (
        not isinstance(item_id, str)
        or not isinstance(change_type, str)
        or not isinstance(state, str)
        or not isinstance(summary, str)
        or not isinstance(entity_id, str)
        or not isinstance(created_at, str)
        or not isinstance(updated_at, str)
    ):
        return None
    if event_starts_at is not None and not isinstance(event_starts_at, str):
        return None
    return AttentionItem(
        id=item_id,
        change_type=change_type,
        state=state,
        summary=summary,
        entity_id=entity_id,
        event_starts_at=event_starts_at,
        created_at=created_at,
        updated_at=updated_at,
    )


def classify_attention_items_response(status_code: int, payload: Any) -> AttentionItemsResult:
    if status_code == 401:
        return AttentionItemsFailure("invalid_auth")
    if status_code == 409:
        return AttentionItemsFailure("household_not_configured")
    if status_code != 200 or not isinstance(payload, list):
        return AttentionItemsFailure("unknown")
    items: list[AttentionItem] = []
    for item_payload in payload:
        item = _attention_item_from(item_payload)
        if item is None:
            return AttentionItemsFailure("unknown")
        items.append(item)
    return items


def classify_attention_item_action_response(status_code: int, payload: Any) -> AttentionItem | ActionFailure:
    if status_code != 200:
        return ActionFailure(reason=_error_reason(status_code, payload))
    item = _attention_item_from(payload)
    if item is None:
        return ActionFailure(reason="malformed response")
    return item


# Epic 7 Story 7.4: documented HA bus events for stable household intent - "purpose-specific
# HA automation hooks" a household can build automations on top of (e.g. flash a light when
# an approval is requested). Kept a fixed, minimal set rather than exposing every possible
# outcome, matching the story's "only when they express stable household intent" scoping.
EVENT_ACTION_EXECUTED = "kinward_action_executed"
EVENT_APPROVAL_REQUESTED = "kinward_approval_requested"
EVENT_APPROVAL_RESOLVED = "kinward_approval_resolved"


@dataclass(frozen=True)
class BusEvent:
    event_type: str
    data: dict[str, Any]


def action_outcome_event(
    result: ActionResult, *, domain: str, service: str, entity_id: str
) -> BusEvent | None:
    """The HA bus event (if any) a ``kinward.request_action`` outcome should fire.

    Only ``executed``/``pending_approval`` are "stable household intent" worth an automation
    hook - ``denied``/``failed`` are rejections, not something that happened in the house, so
    no event fires for them. The payload never includes the caller-supplied ``explanation``
    (private, free-text content) or any person identifier - only the structural HA target,
    matching "hooks avoid leaking private details into HA automation traces".
    """
    if result.outcome == "executed":
        return BusEvent(
            EVENT_ACTION_EXECUTED, {"domain": domain, "service": service, "entity_id": entity_id}
        )
    if result.outcome == "pending_approval" and result.approval_id:
        return BusEvent(
            EVENT_APPROVAL_REQUESTED,
            {
                "approval_id": result.approval_id,
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
            },
        )
    return None


def approval_resolution_event(
    result: ActionResult, *, approval_id: str, decision: Literal["approve", "deny", "cancel"]
) -> BusEvent:
    """The HA bus event for a ``kinward.approve_action``/``kinward.deny_action``/

    ``kinward.cancel_action`` outcome.

    Correlates by ``approval_id`` alone rather than looking up the resolved action's
    domain/service/entity_id - the automation author already has that from whatever created
    the approval in the first place, and this avoids an extra lookup against
    already-resolved (no longer "pending") state.
    """
    return BusEvent(
        EVENT_APPROVAL_RESOLVED,
        {"approval_id": approval_id, "decision": decision, "outcome": result.outcome},
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

    async def async_fetch_people(self) -> PeopleResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/people")
        except (TimeoutError, aiohttp.ClientError):
            return PeopleFailure("cannot_connect")
        return classify_people_response(status, payload)

    async def async_send_conversation_message(
        self,
        *,
        ha_user_id: str,
        text: str,
        conversation_id: str | None,
        language: str,
        device_id: str | None = None,
    ) -> SendMessageResult:
        body = {
            "haUserId": ha_user_id,
            "text": text,
            "conversationId": conversation_id,
            "language": language,
            "deviceId": device_id,
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

    async def async_fetch_assistant_policy(self) -> AssistantPolicyResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/settings/assistant-policy")
        except (TimeoutError, aiohttp.ClientError):
            return AssistantPolicyFailure("cannot_connect")
        return classify_assistant_policy_response(status, payload)

    async def async_update_assistant_policy(
        self, *, max_assistants_per_person: int | None, require_admin_approval_for_creation: bool
    ) -> AssistantPolicyResult:
        body = {
            "maxAssistantsPerPerson": max_assistants_per_person,
            "requireAdminApprovalForCreation": require_admin_approval_for_creation,
        }
        try:
            status, payload = await self._request(
                "PATCH", "/api/v1/integration/settings/assistant-policy", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantPolicyFailure("cannot_connect")
        return classify_assistant_policy_response(status, payload)

    async def async_fetch_tool_policy(self) -> ToolPolicyResult:
        try:
            status, payload = await self._request(
                "GET", "/api/v1/integration/settings/home-assistant-tool-policy"
            )
        except (TimeoutError, aiohttp.ClientError):
            return ToolPolicyFailure("cannot_connect")
        return classify_tool_policy_response(status, payload)

    async def async_update_tool_policy(self, *, permissions: dict[str, str]) -> ToolPolicyResult:
        try:
            status, payload = await self._request(
                "PATCH",
                "/api/v1/integration/settings/home-assistant-tool-policy",
                json_body={"permissions": permissions},
            )
        except (TimeoutError, aiohttp.ClientError):
            return ToolPolicyFailure("cannot_connect")
        return classify_tool_policy_response(status, payload)

    async def async_list_resource_labels(self) -> ResourceLabelsResult:
        try:
            status, payload = await self._request(
                "GET", "/api/v1/integration/settings/home-assistant-resource-labels"
            )
        except (TimeoutError, aiohttp.ClientError):
            return ResourceLabelFailure("cannot_connect")
        return classify_resource_labels_response(status, payload)

    async def async_set_resource_label(self, *, entity_id: str, label: str) -> ResourceLabelResult:
        try:
            status, payload = await self._request(
                "PUT",
                "/api/v1/integration/settings/home-assistant-resource-labels",
                json_body={"entityId": entity_id, "label": label},
            )
        except (TimeoutError, aiohttp.ClientError):
            return ResourceLabelFailure("cannot_connect")
        return classify_resource_label_response(status, payload)

    async def async_delete_resource_label(self, *, entity_id: str) -> ResourceLabelFailure | None:
        try:
            status, payload = await self._request(
                "DELETE",
                f"/api/v1/integration/settings/home-assistant-resource-labels/{quote(entity_id)}",
            )
        except (TimeoutError, aiohttp.ClientError):
            return ResourceLabelFailure("cannot_connect")
        if status == 204:
            return None
        if status == 401:
            return ResourceLabelFailure("invalid_auth")
        if status == 409:
            return ResourceLabelFailure("household_not_configured")
        return ResourceLabelFailure("unknown")

    async def async_list_assistants(self, *, ha_user_id: str) -> list[Assistant] | AssistantActionFailure:
        try:
            status, payload = await self._request(
                "GET", f"/api/v1/integration/assistants?haUserId={quote(ha_user_id)}"
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_list_assistants_response(status, payload)

    async def async_create_assistant(
        self, *, ha_user_id: str, name: str, personality: dict[str, Any] | None = None
    ) -> Assistant | AssistantActionFailure:
        body: dict[str, Any] = {"haUserId": ha_user_id, "name": name}
        if personality is not None:
            body["personality"] = personality
        try:
            status, payload = await self._request(
                "POST", "/api/v1/integration/assistants", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_assistant_action_response(status, payload)

    async def async_delete_assistant(
        self, *, ha_user_id: str, assistant_id: str
    ) -> AssistantActionFailure | None:
        try:
            status, payload = await self._request(
                "DELETE",
                f"/api/v1/integration/assistants/{quote(assistant_id)}?haUserId={quote(ha_user_id)}",
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_delete_assistant_response(status, payload)

    async def async_update_assistant_access(
        self,
        *,
        ha_user_id: str,
        assistant_id: str,
        access_mode: str,
        allowed_person_ids: list[str],
    ) -> Assistant | AssistantActionFailure:
        """Set who besides the owner may address this assistant (ADR-002)."""
        body = {
            "haUserId": ha_user_id,
            "accessMode": access_mode,
            "allowedPersonIds": allowed_person_ids,
        }
        try:
            status, payload = await self._request(
                "PATCH", f"/api/v1/integration/assistants/{quote(assistant_id)}", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_assistant_action_response(status, payload)

    async def async_fetch_assistant_identities(
        self,
    ) -> list[AssistantIdentity] | AssistantIdentitiesFailure:
        """Every household assistant's public identity fields (Epic 3 Story 3.7) - never

        personality, so no ``ha_user_id`` scoping is needed (mirrors ``async_fetch_people``).
        """
        try:
            status, payload = await self._request("GET", "/api/v1/integration/assistants/household")
        except (TimeoutError, aiohttp.ClientError):
            return AssistantIdentitiesFailure(error="cannot_connect")
        return classify_assistant_identities_response(status, payload)

    async def async_list_visual_packs(self) -> list[VisualPack] | VisualPacksFailure:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/visual-packs")
        except (TimeoutError, aiohttp.ClientError):
            return VisualPacksFailure(error="cannot_connect")
        return classify_visual_packs_response(status, payload)

    async def async_restart_interview(
        self, *, ha_user_id: str, assistant_id: str
    ) -> Assistant | AssistantActionFailure:
        body = {"haUserId": ha_user_id}
        try:
            status, payload = await self._request(
                "POST",
                f"/api/v1/integration/assistants/{quote(assistant_id)}/interview/restart",
                json_body=body,
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_assistant_action_response(status, payload)

    async def async_import_persona(
        self, *, ha_user_id: str, assistant_id: str, document_text: str
    ) -> PersonaImportProposal | PersonaImportFailure:
        """Step one of Story 3.6 - proposes only, never commits anything."""
        body = {"haUserId": ha_user_id, "documentText": document_text}
        try:
            status, payload = await self._request(
                "POST",
                f"/api/v1/integration/assistants/{quote(assistant_id)}/persona-import",
                json_body=body,
            )
        except (TimeoutError, aiohttp.ClientError):
            return PersonaImportFailure(error="cannot_connect")
        return classify_persona_import_response(status, payload)

    async def async_confirm_persona_import(
        self,
        *,
        ha_user_id: str,
        assistant_id: str,
        dimensions: dict[str, str],
        grounding_notes: str,
    ) -> Assistant | AssistantActionFailure:
        """Step two of Story 3.6 - commits an owner-confirmed (possibly hand-edited) proposal."""
        body = {"haUserId": ha_user_id, "dimensions": dimensions, "groundingNotes": grounding_notes}
        try:
            status, payload = await self._request(
                "POST",
                f"/api/v1/integration/assistants/{quote(assistant_id)}/persona-import/confirm",
                json_body=body,
            )
        except (TimeoutError, aiohttp.ClientError):
            return AssistantActionFailure(reason="cannot_connect")
        return classify_assistant_action_response(status, payload)

    async def async_request_action(
        self,
        *,
        ha_user_id: str,
        assistant_id: str,
        domain: str,
        service: str,
        entity_id: str,
        explanation: str,
        data: dict[str, Any] | None = None,
    ) -> ActionOutcomeResult:
        """Ask Kinward to submit (or, if the household's tool policy requires it,
        queue for admin approval) an HA service call (Epic 7 Story 7.3).
        """
        body: dict[str, Any] = {
            "haUserId": ha_user_id,
            "assistantId": assistant_id,
            "domain": domain,
            "service": service,
            "entityId": entity_id,
            "explanation": explanation,
        }
        if data is not None:
            body["data"] = data
        try:
            status, payload = await self._request(
                "POST", "/api/v1/integration/actions", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return ActionFailure(reason="cannot_connect")
        return classify_action_result_response(status, payload)

    async def async_list_pending_actions(self) -> PendingActionsResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/actions")
        except (TimeoutError, aiohttp.ClientError):
            return PendingActionsFailure("cannot_connect")
        return classify_pending_actions_response(status, payload)

    async def async_resolve_action(
        self, *, approval_id: str, ha_user_id: str, decision: str
    ) -> ActionOutcomeResult:
        body = {"haUserId": ha_user_id}
        try:
            status, payload = await self._request(
                "POST",
                f"/api/v1/integration/actions/{quote(approval_id)}/{decision}",
                json_body=body,
            )
        except (TimeoutError, aiohttp.ClientError):
            return ActionFailure(reason="cannot_connect")
        return classify_action_result_response(status, payload)

    async def async_fetch_calendar_entities(self) -> CalendarEntitiesResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/settings/calendar-entities")
        except (TimeoutError, aiohttp.ClientError):
            return CalendarEntitiesFailure("cannot_connect")
        return classify_calendar_entities_response(status, payload)

    async def async_set_calendar_entity(
        self, *, entity_id: str, enabled: bool
    ) -> CalendarEntity | ActionFailure:
        body = {"entityId": entity_id, "enabled": enabled}
        try:
            status, payload = await self._request(
                "PUT", "/api/v1/integration/settings/calendar-entities", json_body=body
            )
        except (TimeoutError, aiohttp.ClientError):
            return ActionFailure(reason="cannot_connect")
        return classify_set_calendar_entity_response(status, payload)

    async def async_fetch_attention_items(self) -> AttentionItemsResult:
        try:
            status, payload = await self._request("GET", "/api/v1/integration/calendar/attention")
        except (TimeoutError, aiohttp.ClientError):
            return AttentionItemsFailure("cannot_connect")
        return classify_attention_items_response(status, payload)

    async def _async_resolve_attention_item(
        self, *, ha_user_id: str, item_id: str, decision: Literal["acknowledge", "dismiss"]
    ) -> AttentionItem | ActionFailure:
        body = {"haUserId": ha_user_id}
        try:
            status, payload = await self._request(
                "POST",
                f"/api/v1/integration/calendar/attention/{quote(item_id)}/{decision}",
                json_body=body,
            )
        except (TimeoutError, aiohttp.ClientError):
            return ActionFailure(reason="cannot_connect")
        return classify_attention_item_action_response(status, payload)

    async def async_acknowledge_attention_item(
        self, *, ha_user_id: str, item_id: str
    ) -> AttentionItem | ActionFailure:
        return await self._async_resolve_attention_item(
            ha_user_id=ha_user_id, item_id=item_id, decision="acknowledge"
        )

    async def async_dismiss_attention_item(
        self, *, ha_user_id: str, item_id: str
    ) -> AttentionItem | ActionFailure:
        return await self._async_resolve_attention_item(
            ha_user_id=ha_user_id, item_id=item_id, decision="dismiss"
        )
