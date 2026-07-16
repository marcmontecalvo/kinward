from datetime import datetime, timedelta, timezone

from kinward.domain.pending_action import can_resolve_approval, revalidate_before_execution

NOW = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)
EARLIER = NOW - timedelta(hours=1)


def test_non_admin_cannot_resolve_a_pending_approval() -> None:
    ok, error = can_resolve_approval(
        state="pending", resolver_is_admin=False, expires_at=LATER, now=NOW
    )
    assert ok is None
    assert error is not None
    assert error.code == "admin_required"


def test_admin_can_resolve_a_pending_approval_before_expiry() -> None:
    assert can_resolve_approval(state="pending", resolver_is_admin=True, expires_at=LATER, now=NOW) == (
        True,
        None,
    )


def test_expired_approval_cannot_be_resolved() -> None:
    ok, error = can_resolve_approval(
        state="pending", resolver_is_admin=True, expires_at=EARLIER, now=NOW
    )
    assert ok is None
    assert error is not None
    assert error.code == "expired"


def test_already_resolved_approval_cannot_be_resolved_again() -> None:
    ok, error = can_resolve_approval(
        state="denied", resolver_is_admin=True, expires_at=LATER, now=NOW
    )
    assert ok is None
    assert error is not None
    assert error.code == "not_pending"


def test_expiry_check_takes_priority_over_state_check() -> None:
    """An admin resolving something already expired gets "expired", not "not_pending" -

    the caller (application layer) needs this to know it should transition the
    record to ``expired`` rather than report a generic conflict.
    """
    ok, error = can_resolve_approval(
        state="denied", resolver_is_admin=True, expires_at=EARLIER, now=NOW
    )
    assert ok is None
    assert error is not None
    assert error.code == "expired"


def test_approved_action_may_execute_before_expiry() -> None:
    assert revalidate_before_execution(state="approved", expires_at=LATER, now=NOW) == (True, None)


def test_approved_action_cannot_execute_once_expired() -> None:
    ok, error = revalidate_before_execution(state="approved", expires_at=EARLIER, now=NOW)
    assert ok is None
    assert error is not None
    assert error.code == "expired"


def test_execution_requires_the_approved_state() -> None:
    ok, error = revalidate_before_execution(state="pending", expires_at=LATER, now=NOW)
    assert ok is None
    assert error is not None
    assert error.code == "not_approved"
