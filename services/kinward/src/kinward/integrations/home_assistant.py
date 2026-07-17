from __future__ import annotations

from datetime import datetime
from typing import Any

from kinward.integrations.base import IntegrationClient


class HomeAssistantClient:
    def __init__(self, *, base_url: str | None, token: str | None, transport: Any = None) -> None:
        self.token = token
        self.client = IntegrationClient(name="home-assistant", base_url=base_url, transport=transport)

    @property
    def enabled(self) -> bool:
        return self.client.enabled and bool(self.token)

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    async def states(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        result = await self.client.request_json(
            "GET",
            "/api/states",
            fallback=[],
            headers=self._headers(),
        )
        return result if isinstance(result, list) else []

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        """A single entity's fresh state, for post-submission confirmation (Epic 7 Story 7.3's
        "completion requires a fresh matching HA observation").

        Returns ``None`` when disabled, on any request failure, or when HA has no such entity -
        ``request_json``'s ``fallback=None`` collapses all of these the same way ``call_service``
        already does; callers here only need "did a fresh reading confirm it" vs. not, not why a
        reading is unavailable.
        """
        if not self.enabled:
            return None
        result = await self.client.request_json(
            "GET",
            f"/api/states/{entity_id}",
            fallback=None,
            headers=self._headers(),
        )
        return result if isinstance(result, dict) else None

    async def call_service(
        self,
        *,
        domain: str,
        service: str,
        data: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        """Submit an HA service call, returning HA's changed-states response - or
        ``None`` if the call never went through (disabled, circuit open, network/HTTP
        error).

        This distinction matters (Epic 7 Story 7.3, cross-cutting rule 9: "HA action
        success means submitted"): a non-``None`` result - even an empty list - means
        HA accepted and processed the call, while ``None`` means it never left this
        process. Callers must not conflate the two the way this method's read-only
        sibling ``states()`` safely can (a read has no side effect to lose track of).
        """
        if not self.enabled:
            return None
        result = await self.client.request_json(
            "POST",
            f"/api/services/{domain}/{service}",
            fallback=None,
            headers=self._headers(),
            json=data,
        )
        if result is None:
            return None
        return result if isinstance(result, list) else []

    async def list_calendar_entities(self) -> list[str]:
        """Every ``calendar.*`` entity currently known to HA (Epic 5 Story 5.1: "Kinward
        reads configured Home Assistant calendar entities through a provider-neutral
        calendar adapter"). Filters the same ``/api/states`` read every other Kinward
        HA-state consumer already uses, rather than a second endpoint - HA has no
        calendar-specific "list calendars" REST route beyond that.
        """
        states = await self.states()
        return [
            entity_id
            for state in states
            if isinstance(entity_id := state.get("entity_id"), str) and entity_id.startswith("calendar.")
        ]

    async def calendar_events(
        self, entity_id: str, *, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Events for one calendar entity in ``[start, end)`` via HA's
        ``GET /api/calendars/{entity_id}`` REST route.

        Returns ``[]`` when disabled or on any request failure - a calendar sync pass
        that can't currently read a calendar simply treats it as having no events this
        pass, rather than raising; staleness is judged by the caller comparing against
        the previous successful observation, same as every other HA read in this
        module.
        """
        if not self.enabled:
            return []
        result = await self.client.request_json(
            "GET",
            f"/api/calendars/{entity_id}",
            fallback=[],
            headers=self._headers(),
            params={"start": start.isoformat(), "end": end.isoformat()},
        )
        return result if isinstance(result, list) else []

    async def render_template(
        self, template: str, *, variables: dict[str, Any] | None = None
    ) -> str | None:
        """Render a Jinja template through HA's own template engine.

        Used for area-membership lookups (``area_id()``/``area_entities()``) that only HA's
        Jinja environment can answer - not a general templating facility. ``/api/template``
        returns plain text, not JSON, so this uses the client's raw ``request()`` rather than
        ``request_json``.
        """
        if not self.enabled:
            return None
        body: dict[str, Any] = {"template": template}
        if variables:
            body["variables"] = variables
        response = await self.client.request(
            "POST", "/api/template", headers=self._headers(), json=body
        )
        return response.text if response is not None else None
