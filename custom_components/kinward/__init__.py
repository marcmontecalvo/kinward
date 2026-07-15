from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ContextFailure, ContextSuccess, KinwardApiClient
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN
from .coordinator import KinwardDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "conversation"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = KinwardApiClient(
        session, base_url=entry.data[CONF_BASE_URL], token=entry.data[CONF_TOKEN]
    )
    context = await client.async_fetch_context()
    if isinstance(context, ContextFailure):
        raise ConfigEntryNotReady(context.error)
    assert isinstance(context, ContextSuccess)

    coordinator = KinwardDataUpdateCoordinator(hass, client, household_id=context.household_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    async def _handle_refresh(_call: ServiceCall) -> None:
        for stored_coordinator in hass.data.get(DOMAIN, {}).values():
            await stored_coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, "refresh"):
        hass.services.async_register(DOMAIN, "refresh", _handle_refresh)

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "refresh")
    return unloaded
