from kinward.domain.lifecycle import (
    BOOTSTRAP_RECORD_LIFECYCLES,
    TABLE_LIFECYCLE_KEYS,
    UNCLASSIFIED_TABLES,
)
from kinward.persistence.models import Base


def test_every_bootstrap_record_has_explicit_lifecycle_metadata() -> None:
    assert set(BOOTSTRAP_RECORD_LIFECYCLES) == {
        "household",
        "person",
        "child",
        "pet",
        "relationship",
        "primary_assistant",
        "fallback_assistant",
        "setup_capability",
        "bootstrap_attempt",
        "activity",
        "outbox",
        "surface_layout",
        "layout_activation_attempt",
        "provider_settings",
        "assistant_policy",
        "knowledge_fact",
        "approval",
        "home_assistant_tool_policy",
        "home_assistant_resource_label",
        "calendar_entity",
        "calendar_event_observation",
        "attention_item",
    }
    for lifecycle in BOOTSTRAP_RECORD_LIFECYCLES.values():
        assert lifecycle.classification
        assert lifecycle.restore_disposition in {"restore", "quarantine", "regenerate"}
        assert lifecycle.deletion


def test_table_lifecycle_keys_resolve_to_real_taxonomy_entries() -> None:
    for table, keys in TABLE_LIFECYCLE_KEYS.items():
        for key in keys:
            assert key in BOOTSTRAP_RECORD_LIFECYCLES, f"{table} maps to undefined lifecycle key {key!r}"


def test_every_persisted_table_is_classified_or_a_tracked_gap() -> None:
    tables = set(Base.metadata.tables)
    mapped = set(TABLE_LIFECYCLE_KEYS)
    gaps = set(UNCLASSIFIED_TABLES)
    assert not (mapped & gaps), f"tables cannot be both classified and a tracked gap: {mapped & gaps}"
    unaccounted = tables - mapped - gaps
    assert not unaccounted, (
        f"new persisted table(s) {unaccounted} need a lifecycle entry in "
        "TABLE_LIFECYCLE_KEYS (see docs/architecture/data-retention.md) or an "
        "explicit, reasoned entry in UNCLASSIFIED_TABLES"
    )
    assert set(UNCLASSIFIED_TABLES) <= tables, "UNCLASSIFIED_TABLES references a table that no longer exists"


def test_single_class_table_default_classification_matches_taxonomy() -> None:
    for table, keys in TABLE_LIFECYCLE_KEYS.items():
        if len(keys) != 1:
            continue
        column = Base.metadata.tables[table].columns.get("classification")
        if column is None or column.default is None:
            continue
        assert column.default.arg == BOOTSTRAP_RECORD_LIFECYCLES[keys[0]].classification, (
            f"{table}.classification default has drifted from domain/lifecycle.py's {keys[0]!r} entry"
        )
