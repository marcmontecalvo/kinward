from kinward.domain.layout_lifecycle import (
    LAYOUT_LIFECYCLE_POLICY,
    controlled_layout_import_allowed,
    layout_restore_disposition,
)


def test_layout_backup_restore_retention_and_import_are_explicit() -> None:
    assert LAYOUT_LIFECYCLE_POLICY.backup_included is True
    assert LAYOUT_LIFECYCLE_POLICY.controlled_import_eligible is True
    assert "active assignment" in LAYOUT_LIFECYCLE_POLICY.retention
    assert "household reset" in LAYOUT_LIFECYCLE_POLICY.deletion
    assert layout_restore_disposition(
        archive_household_id="household-example",
        target_household_id="household-example",
        schema_major=1,
    ) == "restore"
    assert layout_restore_disposition(
        archive_household_id="household-example-a",
        target_household_id="household-example-b",
        schema_major=1,
    ) == "quarantine"
    assert layout_restore_disposition(
        archive_household_id="household-example",
        target_household_id="household-example",
        schema_major=2,
    ) == "quarantine"
    assert controlled_layout_import_allowed(schema_major=1, contains_executable_fields=False)
    assert not controlled_layout_import_allowed(schema_major=1, contains_executable_fields=True)
