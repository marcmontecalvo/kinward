from __future__ import annotations

from dataclasses import dataclass

# epic-5 Core Concepts: "Attention state tracks the lifecycle of an attention item."
ATTENTION_STATES = frozenset({"active", "acknowledged", "dismissed", "resolved", "expired", "superseded"})

# States where the underlying condition is still considered open - the user has not
# had it closed out from under them by resolution/expiry/supersession. Dismissed is
# still "open" here even though it is hidden from the briefing: epic-5 says a dismissed
# item "remains dismissed unless a new meaningful change occurs" - it can still be
# auto-resolved or superseded like any other live item, just not surfaced meanwhile.
OPEN_STATES = frozenset({"active", "acknowledged", "dismissed"})

CHANGE_TYPES = frozenset(
    {"cancelled", "time_changed", "location_changed", "overlap", "back_to_back", "rsvp_required"}
)


@dataclass(frozen=True)
class InvalidTransition:
    """A requested state change isn't allowed from the item's current state."""

    code: str
    message: str


def can_acknowledge(state: str) -> bool:
    """Acknowledge is idempotent from ``active``/``acknowledged``; anything else (the
    item is no longer open, or already hidden/closed) is not a user-facing action.
    """
    return state in ("active", "acknowledged")


def can_dismiss(state: str) -> bool:
    """Dismiss is allowed from any open state and idempotent if already dismissed."""
    return state in OPEN_STATES


def can_auto_resolve(state: str) -> bool:
    """Kinward may auto-resolve any open item once the underlying issue is gone -
    "Users should not be required to manually resolve calendar issues" applies
    regardless of whether the item was ever seen or dismissed.
    """
    return state in OPEN_STATES


def can_auto_expire(state: str) -> bool:
    """An open item may expire once its useful time window has passed."""
    return state in OPEN_STATES


def can_auto_supersede(state: str) -> bool:
    """An open item may be superseded by a materially different newer condition."""
    return state in OPEN_STATES


#: The state a materially new/worsened change resets an item to, regardless of its
#: prior state - even from ``"acknowledged"``: acknowledging closed out the *previous*
#: version of the condition, not this new one (epic-5: "an item may reappear only when
#: the underlying event changes materially... or the deadline or impact materially
#: worsens").
REACTIVATED_STATE = "active"
