from __future__ import annotations

# Epic 7 Story 7.3: "completion requires a fresh matching HA observation." Only services whose
# resulting state is deterministic from the call alone get an entry here - a "toggle" service
# ends in whichever state the entity wasn't already in, so there is nothing fixed to confirm
# against. Any (domain, service) with no entry here (including every toggle) keeps the older
# "a non-None call_service response is sufficient evidence of completion" behavior.
EXPECTED_STATE_BY_SERVICE: dict[tuple[str, str], str] = {
    ("light", "turn_on"): "on",
    ("light", "turn_off"): "off",
    ("switch", "turn_on"): "on",
    ("switch", "turn_off"): "off",
    ("timer", "start"): "active",
    ("timer", "cancel"): "idle",
    ("timer", "pause"): "paused",
    ("lock", "lock"): "locked",
    ("lock", "unlock"): "unlocked",
    ("alarm_control_panel", "alarm_arm_away"): "armed_away",
    ("alarm_control_panel", "alarm_arm_home"): "armed_home",
    ("alarm_control_panel", "alarm_disarm"): "disarmed",
}


def expected_state_for(*, domain: str, service: str) -> str | None:
    """The HA entity state a successful call to ``(domain, service)`` must leave behind, or
    ``None`` when no deterministic end state exists (e.g. "toggle" services)."""
    return EXPECTED_STATE_BY_SERVICE.get((domain, service))
