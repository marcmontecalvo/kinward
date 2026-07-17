from kinward.domain.tool_permission import (
    DEFAULT_TOOL_PERMISSIONS,
    evaluate_capability,
    resolve_capability,
)


def test_resolve_capability_matches_known_domain_service_pairs() -> None:
    assert resolve_capability(domain="light", service="turn_off") == "control_lights"
    assert resolve_capability(domain="switch", service="toggle") == "control_switches"
    assert resolve_capability(domain="timer", service="cancel") == "manage_household_timers"
    assert resolve_capability(domain="lock", service="unlock") == "control_locks"
    assert (
        resolve_capability(domain="alarm_control_panel", service="alarm_disarm")
        == "control_alarm_system"
    )


def test_resolve_capability_is_none_for_unmapped_pairs() -> None:
    assert resolve_capability(domain="light", service="turn_on_and_upload_credentials") is None
    assert resolve_capability(domain="climate", service="set_temperature") is None
    assert resolve_capability(domain="camera", service="disable_motion_detection") is None


def test_evaluate_capability_denies_unmapped_capability() -> None:
    assert evaluate_capability(capability=None, permissions=DEFAULT_TOOL_PERMISSIONS) == "deny"


def test_evaluate_capability_denies_capability_missing_from_permissions() -> None:
    assert evaluate_capability(capability="control_lights", permissions={}) == "deny"


def test_evaluate_capability_denies_a_malformed_permission_value() -> None:
    assert evaluate_capability(capability="control_lights", permissions={"control_lights": "sure"}) == "deny"


def test_evaluate_capability_reads_the_configured_result() -> None:
    assert (
        evaluate_capability(capability="control_lights", permissions=DEFAULT_TOOL_PERMISSIONS)
        == "allow"
    )
    assert (
        evaluate_capability(capability="control_locks", permissions=DEFAULT_TOOL_PERMISSIONS)
        == "deny"
    )
    assert (
        evaluate_capability(
            capability="control_locks", permissions={"control_locks": "approval_required"}
        )
        == "approval_required"
    )


def test_default_permissions_cover_every_known_capability() -> None:
    from kinward.domain.tool_permission import CAPABILITY_SERVICE_ALLOWLIST

    assert set(DEFAULT_TOOL_PERMISSIONS) == set(CAPABILITY_SERVICE_ALLOWLIST)
