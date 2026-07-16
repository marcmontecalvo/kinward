from __future__ import annotations

from typing import Sequence


def can_address_assistant(
    *,
    owner_person_id: str | None,
    access_mode: str,
    allowed_person_ids: Sequence[str],
    caller_person_id: str,
) -> bool:
    """Whether ``caller_person_id`` may address this assistant at all (ADR-002).

    This governs access to the assistant only. It never affects which
    conversational-memory peer is used - that's the existing, unconditional
    ``(person, assistant)`` session keying, unaffected by who's allowed to
    start it - and it never grants a tool permission; both are separate,
    still-unbuilt concerns per ADR-002.

    ``owner_only``: only the owner. ``household``: any resolved person (a
    single-household deployment has no household boundary left to check once
    someone has resolved to a person at all - the household-fallback assistant,
    which has no owner, always uses this mode). ``allowlist``: the owner plus
    exactly the listed person ids.
    """
    if owner_person_id is not None and owner_person_id == caller_person_id:
        return True
    if access_mode == "household":
        return True
    if access_mode == "allowlist":
        return caller_person_id in allowed_person_ids
    return False
