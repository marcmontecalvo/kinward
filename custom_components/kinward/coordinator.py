from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .api import (
    AttentionItem,
    AttentionItemsFailure,
    HaPerson,
    KinwardApiClient,
    PendingAction,
    PendingActionsFailure,
    Pet,
    PetsFailure,
    SummaryFailure,
    SummarySuccess,
    SyncedPerson,
    SyncPeopleFailure,
    SyncPeopleSuccess,
)
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KinwardDataUpdateCoordinator(DataUpdateCoordinator[SummarySuccess]):
    """Coordinates a single poll of /api/v1/integration/summary for every Kinward entity.

    Each poll also syncs Home Assistant's own ``person.*`` entities to the backend - this is
    Kinward's only identity source (no invitations, no admin mapping step). A sync failure is
    logged and never blocks the summary refresh entities depend on for availability.
    """

    def __init__(
        self, hass: HomeAssistant, client: KinwardApiClient, *, household_id: str
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL)
        self._client = client
        self.household_id = household_id
        self.last_success_at: datetime | None = None
        self.people: list[SyncedPerson] = []
        self.pets: list[Pet] = []
        self.pending_actions: list[PendingAction] = []
        self.attention_items: list[AttentionItem] = []

    @property
    def client(self) -> KinwardApiClient:
        return self._client

    async def _async_sync_people(self) -> None:
        people: list[HaPerson] = []
        for state in self.hass.states.async_all("person"):
            ha_person_id = state.attributes.get("id")
            if not isinstance(ha_person_id, str):
                continue
            ha_user_id = state.attributes.get("user_id")
            ha_user_id = ha_user_id if isinstance(ha_user_id, str) else None
            is_admin = False
            if ha_user_id is not None:
                ha_user = await self.hass.auth.async_get_user(ha_user_id)
                is_admin = ha_user is not None and ha_user.is_admin
            people.append(
                HaPerson(
                    ha_person_id=ha_person_id,
                    ha_user_id=ha_user_id,
                    display_name=state.attributes.get("friendly_name") or state.name,
                    is_admin=is_admin,
                )
            )
        result = await self._client.async_sync_people(people)
        if isinstance(result, SyncPeopleFailure):
            _LOGGER.warning("Kinward person sync failed: %s", result.error)
            return
        assert isinstance(result, SyncPeopleSuccess)
        self.people = result.people

    async def _async_fetch_pets(self) -> None:
        result = await self._client.async_fetch_pets()
        if isinstance(result, PetsFailure):
            _LOGGER.warning("Kinward pets fetch failed: %s", result.error)
            return
        self.pets = result.pets

    async def _async_fetch_pending_actions(self) -> None:
        result = await self._client.async_list_pending_actions()
        if isinstance(result, PendingActionsFailure):
            _LOGGER.warning("Kinward pending actions fetch failed: %s", result.error)
            return
        self.pending_actions = result

    async def _async_fetch_attention_items(self) -> None:
        result = await self._client.async_fetch_attention_items()
        if isinstance(result, AttentionItemsFailure):
            _LOGGER.warning("Kinward attention items fetch failed: %s", result.error)
            return
        self.attention_items = result

    async def _async_update_data(self) -> SummarySuccess:
        await self._async_sync_people()
        await self._async_fetch_pets()
        await self._async_fetch_pending_actions()
        await self._async_fetch_attention_items()
        result = await self._client.async_fetch_summary()
        if isinstance(result, SummaryFailure):
            if result.error == "invalid_auth":
                raise ConfigEntryAuthFailed(result.error)
            raise UpdateFailed(result.error)
        self.last_success_at = dt_util.utcnow()
        return result
