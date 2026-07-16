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
}
