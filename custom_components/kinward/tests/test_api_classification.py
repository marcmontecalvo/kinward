from __future__ import annotations

from kinward.api import (
    Assistant,
    AssistantActionFailure,
    AssistantPolicy,
    AssistantPolicyFailure,
    AttentionStatus,
    BriefingStatus,
    ContextFailure,
    ContextSuccess,
    NextEventStatus,
    PeopleFailure,
    Person,
    Pet,
    PetsFailure,
    PetsSuccess,
    ProviderSettings,
    ProviderSettingsFailure,
    SendMessageFailure,
    SendMessageSuccess,
    SummaryFailure,
    SummarySuccess,
    SyncedPerson,
    SyncPeopleFailure,
    SyncPeopleSuccess,
    classify_assistant_action_response,
    classify_assistant_policy_response,
    classify_context_response,
    classify_delete_assistant_response,
    classify_list_assistants_response,
    classify_people_response,
    classify_pets_response,
    classify_provider_settings_response,
    classify_send_message_response,
    classify_summary_response,
    classify_sync_people_response,
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
