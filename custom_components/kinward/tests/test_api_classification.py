from __future__ import annotations

from kinward.api import (
    ActionFailure,
    ActionResult,
    Assistant,
    AssistantActionFailure,
    AssistantIdentitiesFailure,
    AssistantIdentity,
    AssistantPolicy,
    AssistantPolicyFailure,
    AttentionItem,
    AttentionItemsFailure,
    AttentionStatus,
    BriefingStatus,
    CalendarEntitiesFailure,
    CalendarEntity,
    ContextFailure,
    ContextSuccess,
    NextEventStatus,
    PeopleFailure,
    PendingAction,
    PendingActionsFailure,
    Person,
    PersonaImportFailure,
    PersonaImportProposal,
    Pet,
    PetsFailure,
    PetsSuccess,
    ProviderSettings,
    ProviderSettingsFailure,
    ResourceLabel,
    ResourceLabelFailure,
    SendMessageFailure,
    SendMessageSuccess,
    SummaryFailure,
    SummarySuccess,
    SyncedPerson,
    SyncPeopleFailure,
    SyncPeopleSuccess,
    ToolPolicy,
    ToolPolicyFailure,
    VisualPack,
    VisualPackStage,
    VisualPacksFailure,
    classify_action_result_response,
    classify_assistant_action_response,
    classify_assistant_identities_response,
    classify_assistant_policy_response,
    classify_attention_item_action_response,
    classify_attention_items_response,
    classify_calendar_entities_response,
    classify_context_response,
    classify_delete_assistant_response,
    classify_list_assistants_response,
    classify_pending_actions_response,
    classify_people_response,
    classify_persona_import_response,
    classify_pets_response,
    classify_provider_settings_response,
    classify_resource_label_response,
    classify_resource_labels_response,
    classify_send_message_response,
    classify_set_calendar_entity_response,
    classify_summary_response,
    classify_sync_people_response,
    classify_tool_policy_response,
    classify_visual_packs_response,
)
from kinward.api import (
    EVENT_ACTION_EXECUTED,
    EVENT_APPROVAL_REQUESTED,
    EVENT_APPROVAL_RESOLVED,
    BusEvent,
    action_outcome_event,
    approval_resolution_event,
)


def _context_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "householdId": "household-example",
        "householdName": "Example House",
        "contractVersion": "v1",
    }
    payload.update(overrides)
    return payload


def test_classify_context_response_success() -> None:
    result = classify_context_response(200, _context_payload())
    assert result == ContextSuccess(
        household_id="household-example", household_name="Example House", contract_version="v1"
    )


def test_classify_context_response_incompatible_contract_version() -> None:
    result = classify_context_response(200, _context_payload(contractVersion="v2"))
    assert result == ContextFailure("incompatible_api")


def test_classify_context_response_malformed_success_payload() -> None:
    result = classify_context_response(200, {"householdId": "only-one-field"})
    assert result == ContextFailure("unknown")


def test_classify_context_response_invalid_auth() -> None:
    assert classify_context_response(401, {}) == ContextFailure("invalid_auth")


def test_classify_context_response_household_not_configured() -> None:
    assert classify_context_response(409, {}) == ContextFailure("household_not_configured")


def test_classify_context_response_unexpected_status_is_unknown() -> None:
    assert classify_context_response(500, {}) == ContextFailure("unknown")
    assert classify_context_response(200, "not-a-dict") == ContextFailure("unknown")


def _summary_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "household": {"adultCount": 2, "childCount": 1},
        "briefing": {"state": "intentionally-disabled", "reason": "not-yet-implemented"},
        "attention": {"state": "intentionally-disabled", "reason": "not-yet-implemented"},
        "nextEvent": {"state": "intentionally-disabled", "reason": "not-yet-implemented"},
    }
    payload.update(overrides)
    return payload


def test_classify_summary_response_success() -> None:
    result = classify_summary_response(200, _summary_payload())
    assert isinstance(result, SummarySuccess)
    assert result.adult_count == 2
    assert result.child_count == 1
    assert result.briefing == BriefingStatus(
        state="intentionally-disabled", reason="not-yet-implemented", summary=None
    )
    assert result.attention == AttentionStatus(
        state="intentionally-disabled", reason="not-yet-implemented", count=None
    )
    assert result.next_event == NextEventStatus(
        state="intentionally-disabled", reason="not-yet-implemented", summary=None, starts_at=None
    )


def test_classify_summary_response_carries_real_values_when_available() -> None:
    payload = _summary_payload(
        briefing={"state": "available", "summary": "Quiet morning."},
        attention={"state": "available", "count": 2},
        nextEvent={
            "state": "available",
            "summary": "School pickup",
            "startsAt": "2026-07-16T15:00:00+00:00",
        },
    )
    result = classify_summary_response(200, payload)
    assert isinstance(result, SummarySuccess)
    assert result.briefing.summary == "Quiet morning."
    assert result.attention.count == 2
    assert result.next_event.summary == "School pickup"
    assert result.next_event.starts_at == "2026-07-16T15:00:00+00:00"


def test_classify_summary_response_invalid_auth() -> None:
    assert classify_summary_response(401, {}) == SummaryFailure("invalid_auth")


def test_classify_summary_response_household_not_configured() -> None:
    assert classify_summary_response(409, {}) == SummaryFailure("household_not_configured")


def test_classify_summary_response_missing_household_is_unknown() -> None:
    assert classify_summary_response(200, {}) == SummaryFailure("unknown")


def _synced_person_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "person-1",
        "haPersonId": "ha-person-1",
        "haUserId": "ha-user-1",
        "displayName": "Example Adult",
        "role": "member",
    }
    payload.update(overrides)
    return payload


def test_classify_sync_people_response_success() -> None:
    payload = [_synced_person_payload()]
    assert classify_sync_people_response(200, payload) == SyncPeopleSuccess(
        people=[
            SyncedPerson(
                id="person-1",
                ha_person_id="ha-person-1",
                ha_user_id="ha-user-1",
                display_name="Example Adult",
                role="member",
            )
        ]
    )


def test_classify_sync_people_response_person_with_no_login() -> None:
    payload = [_synced_person_payload(haUserId=None)]
    result = classify_sync_people_response(200, payload)
    assert isinstance(result, SyncPeopleSuccess)
    assert result.people[0].ha_user_id is None


def test_classify_sync_people_response_empty_list() -> None:
    assert classify_sync_people_response(200, []) == SyncPeopleSuccess(people=[])


def test_classify_sync_people_response_malformed_item_is_unknown() -> None:
    assert classify_sync_people_response(200, [{"id": "person-1"}]) == SyncPeopleFailure("unknown")


def test_classify_sync_people_response_invalid_auth() -> None:
    assert classify_sync_people_response(401, []) == SyncPeopleFailure("invalid_auth")


def test_classify_sync_people_response_household_not_configured() -> None:
    assert classify_sync_people_response(409, []) == SyncPeopleFailure("household_not_configured")


def test_classify_sync_people_response_reports_admin_role() -> None:
    payload = [_synced_person_payload(role="admin")]
    result = classify_sync_people_response(200, payload)
    assert isinstance(result, SyncPeopleSuccess)
    assert result.people[0].role == "admin"


def _pet_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "pet-1",
        "displayName": "Biscuit",
        "species": "Dog",
        "sharedFacts": ["Needs a walk every morning"],
    }
    payload.update(overrides)
    return payload


def test_classify_pets_response_success() -> None:
    payload = [_pet_payload()]
    assert classify_pets_response(200, payload) == PetsSuccess(
        pets=[
            Pet(
                id="pet-1",
                display_name="Biscuit",
                species="Dog",
                shared_facts=["Needs a walk every morning"],
            )
        ]
    )


def test_classify_pets_response_empty_list() -> None:
    assert classify_pets_response(200, []) == PetsSuccess(pets=[])


def test_classify_pets_response_malformed_item_is_unknown() -> None:
    assert classify_pets_response(200, [{"id": "pet-1"}]) == PetsFailure("unknown")


def test_classify_pets_response_invalid_auth() -> None:
    assert classify_pets_response(401, []) == PetsFailure("invalid_auth")


def test_classify_pets_response_household_not_configured() -> None:
    assert classify_pets_response(409, []) == PetsFailure("household_not_configured")


def test_classify_send_message_response_mapped_success() -> None:
    payload = {
        "conversationId": "topic-1",
        "outcome": "completed",
        "responseText": "hello back",
        "mapped": True,
    }
    assert classify_send_message_response(200, payload) == SendMessageSuccess(
        conversation_id="topic-1", outcome="completed", response_text="hello back", mapped=True
    )


def test_classify_send_message_response_unmapped_has_no_conversation_id() -> None:
    payload = {
        "conversationId": None,
        "outcome": "unmapped",
        "responseText": "not linked yet",
        "mapped": False,
    }
    assert classify_send_message_response(200, payload) == SendMessageSuccess(
        conversation_id=None, outcome="unmapped", response_text="not linked yet", mapped=False
    )


def test_classify_send_message_response_invalid_auth() -> None:
    assert classify_send_message_response(401, {}) == SendMessageFailure("invalid_auth")


def test_classify_send_message_response_malformed_is_unknown() -> None:
    assert classify_send_message_response(200, {"outcome": "completed"}) == SendMessageFailure(
        "unknown"
    )


def _provider_settings_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "modelProvider": "none",
        "modelBaseUrl": None,
        "modelName": None,
        "hasModelApiKey": False,
        "memoryBackend": "none",
        "honchoUrl": None,
        "knowledgeBackend": "none",
        "llmWikiUrl": None,
    }
    payload.update(overrides)
    return payload


def test_classify_provider_settings_response_defaults() -> None:
    result = classify_provider_settings_response(200, _provider_settings_payload())
    assert result == ProviderSettings(
        model_provider="none",
        model_base_url=None,
        model_name=None,
        has_model_api_key=False,
        memory_backend="none",
        honcho_url=None,
        knowledge_backend="none",
        llm_wiki_url=None,
    )


def test_classify_provider_settings_response_configured() -> None:
    payload = _provider_settings_payload(
        modelProvider="openai",
        modelBaseUrl="https://api.openai.com/v1",
        modelName="gpt-5",
        hasModelApiKey=True,
        memoryBackend="honcho",
        honchoUrl="http://honcho.local:8000",
    )
    result = classify_provider_settings_response(200, payload)
    assert isinstance(result, ProviderSettings)
    assert result.model_provider == "openai"
    assert result.model_base_url == "https://api.openai.com/v1"
    assert result.has_model_api_key is True
    assert result.memory_backend == "honcho"
    assert result.honcho_url == "http://honcho.local:8000"


def test_classify_provider_settings_response_invalid_auth() -> None:
    assert classify_provider_settings_response(401, {}) == ProviderSettingsFailure("invalid_auth")


def test_classify_provider_settings_response_household_not_configured() -> None:
    assert classify_provider_settings_response(409, {}) == ProviderSettingsFailure(
        "household_not_configured"
    )


def test_classify_provider_settings_response_malformed_is_unknown() -> None:
    assert classify_provider_settings_response(200, {"modelProvider": "openai"}) == (
        ProviderSettingsFailure("unknown")
    )


def test_classify_assistant_policy_response_defaults() -> None:
    payload = {"maxAssistantsPerPerson": None, "requireAdminApprovalForCreation": False}
    assert classify_assistant_policy_response(200, payload) == AssistantPolicy(
        max_assistants_per_person=None, require_admin_approval_for_creation=False
    )


def test_classify_assistant_policy_response_configured() -> None:
    payload = {"maxAssistantsPerPerson": 3, "requireAdminApprovalForCreation": True}
    assert classify_assistant_policy_response(200, payload) == AssistantPolicy(
        max_assistants_per_person=3, require_admin_approval_for_creation=True
    )


def test_classify_assistant_policy_response_invalid_auth() -> None:
    assert classify_assistant_policy_response(401, {}) == AssistantPolicyFailure("invalid_auth")


def test_classify_tool_policy_response_success() -> None:
    payload = {
        "permissions": {
            "control_lights": "allow",
            "control_switches": "allow",
            "manage_household_timers": "allow",
            "control_locks": "deny",
            "control_alarm_system": "deny",
        }
    }
    result = classify_tool_policy_response(200, payload)
    assert result == ToolPolicy(permissions=payload["permissions"])


def test_classify_tool_policy_response_invalid_auth() -> None:
    assert classify_tool_policy_response(401, {}) == ToolPolicyFailure("invalid_auth")


def test_classify_tool_policy_response_household_not_configured() -> None:
    assert classify_tool_policy_response(409, {}) == ToolPolicyFailure("household_not_configured")


def test_classify_tool_policy_response_malformed_is_unknown() -> None:
    assert classify_tool_policy_response(200, {"permissions": "not-a-dict"}) == ToolPolicyFailure(
        "unknown"
    )
    assert classify_tool_policy_response(200, {}) == ToolPolicyFailure("unknown")
    assert classify_tool_policy_response(
        200, {"permissions": {"control_lights": 1}}
    ) == ToolPolicyFailure("unknown")


def _resource_label_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "entityId": "light.kitchen",
        "label": "Kitchen light",
        "recordVersion": 1,
    }
    payload.update(overrides)
    return payload


def test_classify_resource_labels_response_success() -> None:
    result = classify_resource_labels_response(200, [_resource_label_payload()])
    assert result == [
        ResourceLabel(entity_id="light.kitchen", label="Kitchen light", record_version=1)
    ]


def test_classify_resource_labels_response_empty_list() -> None:
    assert classify_resource_labels_response(200, []) == []


def test_classify_resource_labels_response_malformed_item_is_unknown() -> None:
    assert classify_resource_labels_response(
        200, [{"entityId": "light.kitchen"}]
    ) == ResourceLabelFailure("unknown")


def test_classify_resource_labels_response_invalid_auth() -> None:
    assert classify_resource_labels_response(401, []) == ResourceLabelFailure("invalid_auth")


def test_classify_resource_labels_response_household_not_configured() -> None:
    assert classify_resource_labels_response(409, []) == ResourceLabelFailure(
        "household_not_configured"
    )


def test_classify_resource_label_response_success() -> None:
    result = classify_resource_label_response(200, _resource_label_payload())
    assert result == ResourceLabel(entity_id="light.kitchen", label="Kitchen light", record_version=1)


def test_classify_resource_label_response_malformed_is_unknown() -> None:
    assert classify_resource_label_response(200, {"entityId": "light.kitchen"}) == (
        ResourceLabelFailure("unknown")
    )


def test_classify_resource_label_response_invalid_auth() -> None:
    assert classify_resource_label_response(401, {}) == ResourceLabelFailure("invalid_auth")


def test_classify_people_response_success() -> None:
    payload = [{"id": "person-1", "displayName": "Marc"}, {"id": "person-2", "displayName": "Lisa"}]
    assert classify_people_response(200, payload) == [
        Person(id="person-1", display_name="Marc"),
        Person(id="person-2", display_name="Lisa"),
    ]


def test_classify_people_response_invalid_auth() -> None:
    assert classify_people_response(401, {}) == PeopleFailure("invalid_auth")


def test_classify_people_response_malformed_is_unknown() -> None:
    assert classify_people_response(200, [{"id": "person-1"}]) == PeopleFailure("unknown")


def _assistant_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "assistant-1",
        "name": "Calopex",
        "personality": {},
        "accessMode": "owner_only",
        "allowedPersonIds": [],
        "visualPackId": "orb",
        "interviewState": "completed",
        "visualStage": "formed",
    }
    payload.update(overrides)
    return payload


def _assistant(**overrides: object) -> Assistant:
    defaults: dict[str, object] = {
        "id": "assistant-1",
        "name": "Calopex",
        "personality": {},
        "access_mode": "owner_only",
        "allowed_person_ids": [],
        "visual_pack_id": "orb",
        "interview_state": "completed",
        "visual_stage": "formed",
    }
    defaults.update(overrides)
    return Assistant(**defaults)  # type: ignore[arg-type]


def test_classify_list_assistants_response_success() -> None:
    result = classify_list_assistants_response(200, [_assistant_payload()])
    assert result == [_assistant()]


def test_classify_list_assistants_response_malformed_is_a_failure() -> None:
    result = classify_list_assistants_response(200, {"not": "a list"})
    assert isinstance(result, AssistantActionFailure)


def test_classify_assistant_action_response_success() -> None:
    result = classify_assistant_action_response(201, _assistant_payload())
    assert result == _assistant()


def test_classify_assistant_action_response_carries_access_mode_and_allowlist() -> None:
    result = classify_assistant_action_response(
        200, _assistant_payload(accessMode="allowlist", allowedPersonIds=["person-2"])
    )
    assert result == _assistant(access_mode="allowlist", allowed_person_ids=["person-2"])


def test_classify_assistant_action_response_policy_blocked_carries_the_message() -> None:
    payload = {"detail": {"code": "max_assistants_reached", "message": "This person already has the maximum of 1 assistants."}}
    result = classify_assistant_action_response(409, payload)
    assert result == AssistantActionFailure(
        reason="This person already has the maximum of 1 assistants."
    )


def test_classify_delete_assistant_response_success_is_no_content() -> None:
    assert classify_delete_assistant_response(204, None) is None


def test_classify_delete_assistant_response_failure_carries_the_code() -> None:
    payload = {"detail": {"code": "last_assistant"}}
    result = classify_delete_assistant_response(409, payload)
    assert result == AssistantActionFailure(reason="last_assistant")


def _pending_action_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "approval-1",
        "requestedByPersonId": "person-1",
        "action": "home_assistant.lock.unlock",
        "explanation": "Let the dog walker in.",
        "domain": "lock",
        "service": "unlock",
        "entityId": "lock.front_door",
        "createdAt": "2026-07-16T12:00:00+00:00",
        "expiresAt": "2026-07-17T12:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_classify_pending_actions_response_success() -> None:
    result = classify_pending_actions_response(200, [_pending_action_payload()])
    assert result == [
        PendingAction(
            id="approval-1",
            requested_by_person_id="person-1",
            action="home_assistant.lock.unlock",
            explanation="Let the dog walker in.",
            domain="lock",
            service="unlock",
            entity_id="lock.front_door",
            created_at="2026-07-16T12:00:00+00:00",
            expires_at="2026-07-17T12:00:00+00:00",
        )
    ]


def test_classify_pending_actions_response_empty_list() -> None:
    assert classify_pending_actions_response(200, []) == []


def test_classify_pending_actions_response_malformed_item_is_unknown() -> None:
    assert classify_pending_actions_response(200, [{"id": "approval-1"}]) == PendingActionsFailure(
        "unknown"
    )


def test_classify_pending_actions_response_invalid_auth() -> None:
    assert classify_pending_actions_response(401, []) == PendingActionsFailure("invalid_auth")


def test_classify_pending_actions_response_household_not_configured() -> None:
    assert classify_pending_actions_response(409, []) == PendingActionsFailure(
        "household_not_configured"
    )


def test_classify_action_result_response_executed() -> None:
    result = classify_action_result_response(200, {"outcome": "executed"})
    assert result == ActionResult(outcome="executed", approval_id=None)


def test_classify_action_result_response_pending_approval_carries_the_id() -> None:
    result = classify_action_result_response(
        200, {"outcome": "pending_approval", "approvalId": "approval-1"}
    )
    assert result == ActionResult(outcome="pending_approval", approval_id="approval-1")


def test_classify_action_result_response_denied_carries_the_reason() -> None:
    payload = {"detail": {"code": "admin_required", "message": "Only a household administrator may resolve this."}}
    result = classify_action_result_response(403, payload)
    assert result == ActionFailure(reason="Only a household administrator may resolve this.")


def test_classify_action_result_response_unexpected_status_is_unknown() -> None:
    assert classify_action_result_response(500, {}) == ActionFailure(reason="unexpected status 500")
    assert classify_action_result_response(200, "not-a-dict") == ActionFailure(
        reason="unexpected status 200"
    )


def test_action_outcome_event_fires_executed_with_no_private_details() -> None:
    result = ActionResult(outcome="executed", approval_id=None)
    event = action_outcome_event(result, domain="light", service="turn_off", entity_id="light.office")
    assert event == BusEvent(
        EVENT_ACTION_EXECUTED,
        {"domain": "light", "service": "turn_off", "entity_id": "light.office"},
    )


def test_action_outcome_event_fires_approval_requested_with_the_approval_id() -> None:
    result = ActionResult(outcome="pending_approval", approval_id="approval-1")
    event = action_outcome_event(result, domain="lock", service="unlock", entity_id="lock.front_door")
    assert event == BusEvent(
        EVENT_APPROVAL_REQUESTED,
        {
            "approval_id": "approval-1",
            "domain": "lock",
            "service": "unlock",
            "entity_id": "lock.front_door",
        },
    )


def test_action_outcome_event_is_none_for_denied_or_failed_outcomes() -> None:
    denied = ActionResult(outcome="denied", approval_id=None)
    failed = ActionResult(outcome="failed", approval_id=None)
    assert action_outcome_event(denied, domain="lock", service="unlock", entity_id="lock.front_door") is None
    assert action_outcome_event(failed, domain="light", service="turn_off", entity_id="light.office") is None


def test_approval_resolution_event_carries_approval_id_decision_and_outcome() -> None:
    result = ActionResult(outcome="executed", approval_id=None)
    event = approval_resolution_event(result, approval_id="approval-1", decision="approve")
    assert event == BusEvent(
        EVENT_APPROVAL_RESOLVED,
        {"approval_id": "approval-1", "decision": "approve", "outcome": "executed"},
    )

    denied_result = ActionResult(outcome="denied", approval_id=None)
    deny_event = approval_resolution_event(denied_result, approval_id="approval-1", decision="deny")
    assert deny_event == BusEvent(
        EVENT_APPROVAL_RESOLVED,
        {"approval_id": "approval-1", "decision": "deny", "outcome": "denied"},
    )

    cancelled_result = ActionResult(outcome="cancelled", approval_id=None)
    cancel_event = approval_resolution_event(
        cancelled_result, approval_id="approval-1", decision="cancel"
    )
    assert cancel_event == BusEvent(
        EVENT_APPROVAL_RESOLVED,
        {"approval_id": "approval-1", "decision": "cancel", "outcome": "cancelled"},
    )


def _calendar_entity_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"entityId": "calendar.family", "enabled": True, "knownToHa": True}
    payload.update(overrides)
    return payload


def test_classify_calendar_entities_response_success() -> None:
    result = classify_calendar_entities_response(200, [_calendar_entity_payload()])
    assert result == [CalendarEntity(entity_id="calendar.family", enabled=True, known_to_ha=True)]


def test_classify_calendar_entities_response_empty_list() -> None:
    assert classify_calendar_entities_response(200, []) == []


def test_classify_calendar_entities_response_malformed_item_is_unknown() -> None:
    assert classify_calendar_entities_response(200, [{"entityId": "calendar.family"}]) == (
        CalendarEntitiesFailure("unknown")
    )


def test_classify_calendar_entities_response_invalid_auth() -> None:
    assert classify_calendar_entities_response(401, []) == CalendarEntitiesFailure("invalid_auth")


def test_classify_calendar_entities_response_household_not_configured() -> None:
    assert classify_calendar_entities_response(409, []) == CalendarEntitiesFailure(
        "household_not_configured"
    )


def test_classify_set_calendar_entity_response_success() -> None:
    result = classify_set_calendar_entity_response(200, _calendar_entity_payload(enabled=False))
    assert result == CalendarEntity(entity_id="calendar.family", enabled=False, known_to_ha=True)


def test_classify_set_calendar_entity_response_failure_carries_the_code() -> None:
    payload = {"detail": {"code": "invalid_entity_id"}}
    result = classify_set_calendar_entity_response(422, payload)
    assert result == ActionFailure(reason="invalid_entity_id")


def _attention_item_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "attention-1",
        "changeType": "time_changed",
        "state": "active",
        "summary": "Time changed: Dentist is now 3:00 PM",
        "entityId": "calendar.family",
        "eventStartsAt": "2026-07-21T15:00:00+00:00",
        "createdAt": "2026-07-17T12:00:00+00:00",
        "updatedAt": "2026-07-17T12:05:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_classify_attention_items_response_success() -> None:
    result = classify_attention_items_response(200, [_attention_item_payload()])
    assert result == [
        AttentionItem(
            id="attention-1",
            change_type="time_changed",
            state="active",
            summary="Time changed: Dentist is now 3:00 PM",
            entity_id="calendar.family",
            event_starts_at="2026-07-21T15:00:00+00:00",
            created_at="2026-07-17T12:00:00+00:00",
            updated_at="2026-07-17T12:05:00+00:00",
        )
    ]


def test_classify_attention_items_response_null_event_starts_at() -> None:
    result = classify_attention_items_response(200, [_attention_item_payload(eventStartsAt=None)])
    assert result == [
        AttentionItem(
            id="attention-1",
            change_type="time_changed",
            state="active",
            summary="Time changed: Dentist is now 3:00 PM",
            entity_id="calendar.family",
            event_starts_at=None,
            created_at="2026-07-17T12:00:00+00:00",
            updated_at="2026-07-17T12:05:00+00:00",
        )
    ]


def test_classify_attention_items_response_empty_list() -> None:
    assert classify_attention_items_response(200, []) == []


def test_classify_attention_items_response_malformed_item_is_unknown() -> None:
    assert classify_attention_items_response(200, [{"id": "attention-1"}]) == AttentionItemsFailure(
        "unknown"
    )


def test_classify_attention_items_response_invalid_auth() -> None:
    assert classify_attention_items_response(401, []) == AttentionItemsFailure("invalid_auth")


def test_classify_attention_items_response_household_not_configured() -> None:
    assert classify_attention_items_response(409, []) == AttentionItemsFailure(
        "household_not_configured"
    )


def test_classify_attention_item_action_response_success() -> None:
    result = classify_attention_item_action_response(200, _attention_item_payload(state="acknowledged"))
    assert isinstance(result, AttentionItem)
    assert result.state == "acknowledged"


def test_classify_attention_item_action_response_failure_carries_the_code() -> None:
    payload = {"detail": {"code": "not_open"}}
    result = classify_attention_item_action_response(409, payload)
    assert result == ActionFailure(reason="not_open")


def _assistant_identity_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "assistant-1",
        "name": "Calopex",
        "ownerPersonId": "person-1",
        "visualPackId": "orb",
        "visualStage": "formed",
        "visualStageIcon": "mdi:orbit-variant",
        "visualStagePreviewImage": None,
        "accent": "#6C63FF",
    }
    payload.update(overrides)
    return payload


def test_classify_assistant_identities_response_success() -> None:
    result = classify_assistant_identities_response(200, [_assistant_identity_payload()])
    assert result == [
        AssistantIdentity(
            id="assistant-1",
            name="Calopex",
            owner_person_id="person-1",
            visual_pack_id="orb",
            visual_stage="formed",
            visual_stage_icon="mdi:orbit-variant",
            visual_stage_preview_image=None,
            accent="#6C63FF",
        )
    ]


def test_classify_assistant_identities_response_allows_null_owner_for_shared_assistant() -> None:
    result = classify_assistant_identities_response(
        200, [_assistant_identity_payload(ownerPersonId=None)]
    )
    assert isinstance(result, list)
    assert result[0].owner_person_id is None


def test_classify_assistant_identities_response_never_carries_personality() -> None:
    """The identity payload has no ``personality`` key at all - proves the client

    can't accidentally surface it even if a future backend response included it.
    """
    payload = _assistant_identity_payload()
    payload["personality"] = {"communication_style": "should never reach here"}
    result = classify_assistant_identities_response(200, [payload])
    assert isinstance(result, list)
    assert not hasattr(result[0], "personality")


def test_classify_assistant_identities_response_malformed_is_a_failure() -> None:
    result = classify_assistant_identities_response(200, {"not": "a list"})
    assert isinstance(result, AssistantIdentitiesFailure)


def _visual_pack_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "orb",
        "displayName": "Orb",
        "category": "abstract",
        "defaultAccent": "#6C63FF",
        "stages": [{"name": "quiet", "mdiIcon": "mdi:circle-outline", "previewImage": None}],
    }
    payload.update(overrides)
    return payload


def test_classify_visual_packs_response_success() -> None:
    result = classify_visual_packs_response(200, [_visual_pack_payload()])
    assert result == [
        VisualPack(
            id="orb",
            display_name="Orb",
            category="abstract",
            default_accent="#6C63FF",
            stages=[VisualPackStage(name="quiet", mdi_icon="mdi:circle-outline", preview_image=None)],
        )
    ]


def test_classify_visual_packs_response_malformed_is_a_failure() -> None:
    result = classify_visual_packs_response(200, {"not": "a list"})
    assert isinstance(result, VisualPacksFailure)


def test_classify_persona_import_response_success() -> None:
    payload = {
        "dimensions": {"communication_style": "Direct"},
        "groundingNotes": "Likes dry humor.",
    }
    result = classify_persona_import_response(200, payload)
    assert result == PersonaImportProposal(
        dimensions={"communication_style": "Direct"}, grounding_notes="Likes dry humor."
    )


def test_classify_persona_import_response_malformed_is_a_failure() -> None:
    result = classify_persona_import_response(200, {"not": "the right shape"})
    assert isinstance(result, PersonaImportFailure)


def test_classify_persona_import_response_error_status_is_a_failure() -> None:
    result = classify_persona_import_response(409, {"detail": {"code": "household_not_configured"}})
    assert result == PersonaImportFailure(error="household_not_configured")
