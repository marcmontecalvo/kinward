from kinward.domain.lifecycle import BOOTSTRAP_RECORD_LIFECYCLES


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
    }
    for lifecycle in BOOTSTRAP_RECORD_LIFECYCLES.values():
        assert lifecycle.classification
        assert lifecycle.restore_disposition in {"restore", "quarantine", "regenerate"}
        assert lifecycle.deletion
