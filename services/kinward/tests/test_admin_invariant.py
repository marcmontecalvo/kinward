from kinward.domain.admin_invariant import validate_admin_removal


def test_removing_a_non_admin_is_always_allowed() -> None:
    assert validate_admin_removal(admin_count_before=1, person_being_removed_is_admin=False) == (
        True,
        None,
    )
    assert validate_admin_removal(admin_count_before=0, person_being_removed_is_admin=False) == (
        True,
        None,
    )


def test_removing_one_of_several_admins_is_allowed() -> None:
    assert validate_admin_removal(admin_count_before=2, person_being_removed_is_admin=True) == (
        True,
        None,
    )


def test_removing_the_sole_admin_is_blocked() -> None:
    result, violation = validate_admin_removal(admin_count_before=1, person_being_removed_is_admin=True)
    assert result is None
    assert violation is not None
    assert violation.code == "household_requires_an_admin"
