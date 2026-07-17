from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RecordLifecycle:
    classification: Literal["private-person", "private-child", "household-shared", "system-operational"]
    backup_eligible: bool
    import_eligible: bool
    restore_disposition: Literal["restore", "quarantine", "regenerate"]
    deletion: str


BOOTSTRAP_RECORD_LIFECYCLES: dict[str, RecordLifecycle] = {
    "household": RecordLifecycle("household-shared", True, True, "restore", "delete with deployment reset"),
    "person": RecordLifecycle("private-person", True, True, "quarantine", "delete with profile"),
    "child": RecordLifecycle("private-child", True, True, "quarantine", "delete with profile"),
    "pet": RecordLifecycle("household-shared", True, True, "quarantine", "delete with pet profile"),
    "relationship": RecordLifecycle("household-shared", True, True, "quarantine", "delete with referenced profile"),
    "primary_assistant": RecordLifecycle("private-person", True, False, "quarantine", "delete with owner"),
    "fallback_assistant": RecordLifecycle("household-shared", True, False, "restore", "delete with household"),
    "setup_capability": RecordLifecycle("system-operational", False, False, "regenerate", "delete after terminal setup/reset"),
    "bootstrap_attempt": RecordLifecycle("system-operational", True, False, "restore", "retain with household audit history"),
    "activity": RecordLifecycle("system-operational", True, False, "restore", "retain under operational policy"),
    "outbox": RecordLifecycle("system-operational", True, False, "restore", "delete after delivery retention"),
    "surface_layout": RecordLifecycle("household-shared", True, True, "quarantine", "delete with surface assignment"),
    "layout_activation_attempt": RecordLifecycle("system-operational", True, False, "restore", "retain with layout audit history"),
    "provider_settings": RecordLifecycle(
        "household-shared", True, False, "quarantine", "delete with household"
    ),
    "assistant_policy": RecordLifecycle(
        "household-shared", True, False, "quarantine", "delete with household"
    ),
    "knowledge_fact": RecordLifecycle(
        "private-person",
        True,
        False,
        "quarantine",
        "confirm/reject/expiry/deletion disposes the row; cascades with owner deletion",
    ),
    "approval": RecordLifecycle(
        "system-operational", True, False, "restore", "retain with household audit history"
    ),
    "home_assistant_tool_policy": RecordLifecycle(
        "household-shared", True, False, "quarantine", "delete with household"
    ),
}

# Maps each persisted SQLAlchemy table (kinward.persistence.models) to the
# BOOTSTRAP_RECORD_LIFECYCLES key(s) that classify it. Some tables hold more than
# one lifecycle class distinguished by a row field rather than by table (people
# splits into person/child by profile_kind; assistants splits into
# primary_assistant/fallback_assistant by kind).
TABLE_LIFECYCLE_KEYS: dict[str, tuple[str, ...]] = {
    "households": ("household",),
    "people": ("person", "child"),
    "assistants": ("primary_assistant", "fallback_assistant"),
    "pets": ("pet",),
    "relationships": ("relationship",),
    "setup_capabilities": ("setup_capability",),
    "bootstrap_attempts": ("bootstrap_attempt",),
    "activity": ("activity",),
    "outbox_messages": ("outbox",),
    "surface_layouts": ("surface_layout",),
    "layout_activation_attempts": ("layout_activation_attempt",),
    "provider_settings": ("provider_settings",),
    "assistant_policy": ("assistant_policy",),
    "knowledge_facts": ("knowledge_fact",),
    "approvals": ("approval",),
    "home_assistant_tool_policy": ("home_assistant_tool_policy",),
}

# Persisted tables with no lifecycle entry yet. A table lands here only with an
# explicit reason - this is a tracked gap, not silent drift. See
# docs/architecture/data-retention.md and epics.md Story 9.4 for the retention
# decisions this is waiting on. Adding a new persisted table anywhere else
# without adding it to TABLE_LIFECYCLE_KEYS or here fails
# tests/test_lifecycle.py.
UNCLASSIFIED_TABLES: dict[str, str] = {
    "memory_index": "pivot-era addition; retention not yet decided",
    "worker_heartbeats": "pivot-era addition; retention not yet decided",
    "integration_tokens": "pivot-era addition; retention not yet decided",
    "topics": "pivot-era addition; retention not yet decided",
    "topic_turns": "pivot-era addition; retention not yet decided",
}
