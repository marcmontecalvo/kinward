from __future__ import annotations

from typing import Any


def resolve_label(
    entity_id: str, *, override: str | None = None, attributes: dict[str, Any] | None = None
) -> str:
    """Household-language label for one HA entity (Epic 7 Story 7.1: "ordinary outputs use
    household language").

    Fallback chain, each tier failing safely into the next rather than raising or returning
    nothing: an admin-set override wins; failing that (absent, or empty/whitespace-only - an
    "invalid mapping" that must fail safely rather than display nothing), HA's own
    ``friendly_name`` attribute, since a homeowner already named it in household language
    there; failing that, the raw entity_id itself. This always returns something displayable -
    never blank, never an exception.
    """
    if override is not None and override.strip():
        return override.strip()
    if attributes:
        friendly_name = attributes.get("friendly_name")
        if isinstance(friendly_name, str) and friendly_name.strip():
            return friendly_name.strip()
    return entity_id


def technical_reference(entity_id: str) -> str:
    """The raw HA identifier - for authorized technical-diagnostics surfaces only (Story 7.1:
    "raw entity/service syntax is limited to authorized technical diagnostics"). A distinct
    function, even though it's the identity function today, so call sites document *why* they
    are allowed to show the raw identifier rather than doing so implicitly."""
    return entity_id
