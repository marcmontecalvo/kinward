from dataclasses import dataclass

from kinward.domain.permissions import enforce_child_self_edit, is_child, require_owner


@dataclass
class Membership:
    person_id: str
    role: str


def test_child_edit_policy() -> None:
    assert enforce_child_self_edit(policy="open", is_child=True) == (True, None)

    result, error = enforce_child_self_edit(policy="approval-required", is_child=True)
    assert result is None
    assert error is not None
    assert error.code == "child_self_edit_approval_required"

    result, error = enforce_child_self_edit(policy="admin-only", is_child=True)
    assert result is None
    assert error is not None
    assert error.code == "child_self_edit_not_allowed"


def test_adult_is_not_blocked_by_child_policy() -> None:
    assert enforce_child_self_edit(policy="admin-only", is_child=False) == (True, None)


def test_role_drives_child_detection() -> None:
    assert is_child(role="child", age_years=16)
    assert not is_child(role="teen", age_years=15)
    assert not is_child(role="adult", age_years=None)
    assert is_child(role="unknown", age_years=None)


def test_owner_guard() -> None:
    memberships = [Membership(person_id="a", role="user"), Membership(person_id="b", role="owner")]
    assert require_owner(person_id="b", memberships=memberships) == (True, None)

    result, error = require_owner(person_id="a", memberships=memberships)
    assert result is None
    assert error is not None
    assert error.code == "assistant_owner_required"
