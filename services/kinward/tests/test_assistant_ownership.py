from dataclasses import dataclass

from kinward.domain.assistant_ownership import count_owners, validate_owner_count


@dataclass
class Membership:
    role: str


def test_personal_assistant_requires_one_owner() -> None:
    assert validate_owner_count(assistant_type="personal", owner_count=1) == (True, None)

    result, violation = validate_owner_count(assistant_type="personal", owner_count=0)
    assert result is None
    assert violation is not None
    assert violation.code == "personal_assistant_owner_count"


def test_shared_fallback_has_no_personal_owner() -> None:
    assert validate_owner_count(assistant_type="shared-fallback", owner_count=0) == (True, None)

    result, violation = validate_owner_count(assistant_type="shared-fallback", owner_count=2)
    assert result is None
    assert violation is not None
    assert violation.code == "shared_fallback_owner_count"


def test_count_owners_ignores_non_owner_memberships() -> None:
    memberships = [Membership("owner"), Membership("user"), Membership("observer")]
    assert count_owners(memberships) == 1
