from kinward.domain.attention_item import (
    REACTIVATED_STATE,
    can_acknowledge,
    can_auto_expire,
    can_auto_resolve,
    can_auto_supersede,
    can_dismiss,
)


def test_can_acknowledge_only_from_active_or_already_acknowledged() -> None:
    assert can_acknowledge("active")
    assert can_acknowledge("acknowledged")
    for state in ("dismissed", "resolved", "expired", "superseded"):
        assert not can_acknowledge(state)


def test_can_dismiss_from_any_open_state() -> None:
    for state in ("active", "acknowledged", "dismissed"):
        assert can_dismiss(state)
    for state in ("resolved", "expired", "superseded"):
        assert not can_dismiss(state)


def test_can_auto_resolve_from_any_open_state_including_dismissed() -> None:
    for state in ("active", "acknowledged", "dismissed"):
        assert can_auto_resolve(state)
    for state in ("resolved", "expired", "superseded"):
        assert not can_auto_resolve(state)


def test_can_auto_expire_and_supersede_mirror_open_states() -> None:
    for state in ("active", "acknowledged", "dismissed"):
        assert can_auto_expire(state)
        assert can_auto_supersede(state)
    for state in ("resolved", "expired", "superseded"):
        assert not can_auto_expire(state)
        assert not can_auto_supersede(state)


def test_reactivated_state_is_always_active() -> None:
    assert REACTIVATED_STATE == "active"
