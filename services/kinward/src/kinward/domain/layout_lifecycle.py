from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


LayoutRestoreDisposition = Literal["restore", "quarantine"]


@dataclass(frozen=True)
class LayoutLifecyclePolicy:
    backup_included: bool = True
    controlled_import_eligible: bool = True
    retention: str = "retain active assignment and activation audit with household backup"
    deletion: str = "delete assignment with its surface scope or household reset"


LAYOUT_LIFECYCLE_POLICY = LayoutLifecyclePolicy()


def layout_restore_disposition(
    *, archive_household_id: str, target_household_id: str, schema_major: int
) -> LayoutRestoreDisposition:
    """Fail closed across households and unsupported schema generations."""
    if archive_household_id != target_household_id or schema_major != 1:
        return "quarantine"
    return "restore"


def controlled_layout_import_allowed(*, schema_major: int, contains_executable_fields: bool) -> bool:
    return schema_major == 1 and not contains_executable_fields
