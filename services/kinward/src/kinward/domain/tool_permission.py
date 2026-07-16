from __future__ import annotations

from typing import Literal, Mapping

PermissionResult = Literal["allow", "approval_required", "deny"]

# ADR-002 sec. 4: "tool permissions must be expressed as concrete capabilities
# implemented by code" - the (domain, service) pair HA is actually asked to call is
# what's checked, never a caller-asserted capability label. An unmapped pair has no
# capability at all and is always denied by resolve_capability's caller.
CAPABILITY_SERVICE_ALLOWLIST: dict[str, frozenset[tuple[str, str]]] = {
    "control_lights": frozenset(
        {("light", "turn_on"), ("light", "turn_off"), ("light", "toggle")}
    ),
    "control_switches": frozenset(
        {("switch", "turn_on"), ("switch", "turn_off"), ("switch", "toggle")}
    ),
    "manage_household_timers": frozenset(
        {("timer", "start"), ("timer", "cancel"), ("timer", "pause")}
    ),
    "control_locks": frozenset({("lock", "lock"), ("lock", "unlock")}),
    "control_alarm_system": frozenset(
        {
            ("alarm_control_panel", "alarm_arm_away"),
            ("alarm_control_panel", "alarm_arm_home"),
            ("alarm_control_panel", "alarm_disarm"),
        }
    ),
}

# ADR-002 sec. 4's example split: routine shared-device control defaults to allow;
# higher-risk actions (no per-resource owner to notify, unlike ADR-002 sec. 5's
# calendar case) default to deny. A household admin may loosen either via the
# integration's options flow.
DEFAULT_TOOL_PERMISSIONS: dict[str, PermissionResult] = {
    "control_lights": "allow",
    "control_switches": "allow",
    "manage_household_timers": "allow",
    "control_locks": "deny",
    "control_alarm_system": "deny",
}


def resolve_capability(*, domain: str, service: str) -> str | None:
    """The capability an HA ``(domain, service)`` call belongs to, or ``None`` if unmapped.

    ``None`` means this call matches no known capability at all - the caller must
    treat that as fail-closed deny, never as "no restriction configured".
    """
    for capability, allowed in CAPABILITY_SERVICE_ALLOWLIST.items():
        if (domain, service) in allowed:
            return capability
    return None


def evaluate_capability(
    *, capability: str | None, permissions: Mapping[str, str]
) -> PermissionResult:
    """Fail-closed: an unmapped capability, or one absent from ``permissions``, denies."""
    if capability is None:
        return "deny"
    result = permissions.get(capability)
    if result == "allow":
        return "allow"
    if result == "approval_required":
        return "approval_required"
    return "deny"
