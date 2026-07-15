from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .api import KinwardApiClient, SummaryFailure, SummarySuccess
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KinwardDataUpdateCoordinator(DataUpdateCoordinator[SummarySuccess]):
    """Coordinates a single poll of /api/v1/integration/summary for every Kinward entity."""

    def __init__(
        self, hass: HomeAssistant, client: KinwardApiClient, *, household_id: str
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL)
        self._client = client
        self.household_id = household_id
        self.last_success_at: datetime | None = None

    @property
    def client(self) -> KinwardApiClient:
        return self._client

    async def _async_update_data(self) -> SummarySuccess:
        result = await self._client.async_fetch_summary()
        if isinstance(result, SummaryFailure):
            raise UpdateFailed(result.error)
        self.last_success_at = dt_util.utcnow()
        return result
