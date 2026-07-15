from __future__ import annotations

from kinward.api import (
    AttentionStatus,
    BriefingStatus,
    ContextFailure,
    ContextSuccess,
    HaUserMapping,
    MappingsFailure,
    MappingsSuccess,
    NextEventStatus,
    PeopleFailure,
    PeopleSuccess,
    Person,
    SendMessageFailure,
    SendMessageSuccess,
    SummaryFailure,
    SummarySuccess,
    classify_context_response,
    classify_mappings_response,
    classify_people_response,
    classify_send_message_response,
    classify_summary_response,
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


def test_classify_people_response_success() -> None:
    payload = [{"id": "person-1", "displayName": "Example Adult"}]
    assert classify_people_response(200, payload) == PeopleSuccess(
        people=[Person(id="person-1", display_name="Example Adult")]
    )


def test_classify_people_response_empty_list() -> None:
    assert classify_people_response(200, []) == PeopleSuccess(people=[])


def test_classify_people_response_malformed_item_is_unknown() -> None:
    assert classify_people_response(200, [{"id": "person-1"}]) == PeopleFailure("unknown")


def test_classify_people_response_invalid_auth() -> None:
    assert classify_people_response(401, []) == PeopleFailure("invalid_auth")


def test_classify_mappings_response_success() -> None:
    payload = [{"haUserId": "ha-user-1", "personId": "person-1"}]
    assert classify_mappings_response(200, payload) == MappingsSuccess(
        mappings=[HaUserMapping(ha_user_id="ha-user-1", person_id="person-1")]
    )


def test_classify_mappings_response_empty_list() -> None:
    assert classify_mappings_response(200, []) == MappingsSuccess(mappings=[])


def test_classify_mappings_response_rejected_upsert_is_unknown() -> None:
    assert classify_mappings_response(422, {"detail": {"code": "person_not_account_bearing"}}) == (
        MappingsFailure("unknown")
    )


def test_classify_mappings_response_invalid_auth() -> None:
    assert classify_mappings_response(401, []) == MappingsFailure("invalid_auth")


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
