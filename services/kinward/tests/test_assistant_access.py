from __future__ import annotations

from kinward.domain.assistant_access import can_address_assistant


def test_owner_can_always_address_their_own_assistant() -> None:
    for mode in ("owner_only", "household", "allowlist"):
        assert can_address_assistant(
            owner_person_id="marc",
            access_mode=mode,
            allowed_person_ids=[],
            caller_person_id="marc",
        )


def test_owner_only_denies_everyone_else() -> None:
    assert not can_address_assistant(
        owner_person_id="marc",
        access_mode="owner_only",
        allowed_person_ids=["lisa"],
        caller_person_id="lisa",
    )


def test_household_mode_allows_any_resolved_caller() -> None:
    assert can_address_assistant(
        owner_person_id="marc",
        access_mode="household",
        allowed_person_ids=[],
        caller_person_id="lisa",
    )


def test_household_mode_allows_a_caller_even_with_no_owner() -> None:
    """The household-fallback assistant has no owner and always uses household mode."""
    assert can_address_assistant(
        owner_person_id=None,
        access_mode="household",
        allowed_person_ids=[],
        caller_person_id="lisa",
    )


def test_allowlist_mode_allows_only_listed_people() -> None:
    assert can_address_assistant(
        owner_person_id="marc",
        access_mode="allowlist",
        allowed_person_ids=["lisa"],
        caller_person_id="lisa",
    )
    assert not can_address_assistant(
        owner_person_id="marc",
        access_mode="allowlist",
        allowed_person_ids=["lisa"],
        caller_person_id="someone-else",
    )


def test_allowlist_mode_denies_by_default_when_empty() -> None:
    assert not can_address_assistant(
        owner_person_id="marc",
        access_mode="allowlist",
        allowed_person_ids=[],
        caller_person_id="lisa",
    )
