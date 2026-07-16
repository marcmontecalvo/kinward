from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AssistantActionFailure, ContextFailure, ContextSuccess, KinwardApiClient
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN
from .coordinator import KinwardDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "conversation"]

CREATE_ASSISTANT_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("personality"): dict,
    }
)
DELETE_ASSISTANT_SCHEMA = vol.Schema({vol.Required("name"): cv.string})


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

    async def _handle_create_assistant(call: ServiceCall) -> None:
        """Create another assistant owned by whichever HA user calls this action -

        self-service only, subject to this household's assistant policy (see the
        Kinward integration's options flow).
        """
        ha_user_id = call.context.user_id
        if not ha_user_id:
            raise ServiceValidationError(
                "kinward.create_assistant must be called by an authenticated user."
            )
        for stored_coordinator in hass.data.get(DOMAIN, {}).values():
            result = await stored_coordinator.client.async_create_assistant(
                ha_user_id=ha_user_id,
                name=call.data["name"],
                personality=call.data.get("personality"),
            )
            if isinstance(result, AssistantActionFailure):
                raise ServiceValidationError(result.reason)

    async def _handle_delete_assistant(call: ServiceCall) -> None:
        """Delete one of the calling HA user's own assistants, addressed by name -

        never another person's, and never a person's last remaining assistant.
        """
        ha_user_id = call.context.user_id
        if not ha_user_id:
            raise ServiceValidationError(
                "kinward.delete_assistant must be called by an authenticated user."
            )
        name = call.data["name"]
        for stored_coordinator in hass.data.get(DOMAIN, {}).values():
            listed = await stored_coordinator.client.async_list_assistants(ha_user_id=ha_user_id)
            if isinstance(listed, AssistantActionFailure):
                raise ServiceValidationError(listed.reason)
            match = next((assistant for assistant in listed if assistant.name == name), None)
            if match is None:
                raise ServiceValidationError(f"No assistant named {name!r} for this user.")
            result = await stored_coordinator.client.async_delete_assistant(
                ha_user_id=ha_user_id, assistant_id=match.id
            )
            if isinstance(result, AssistantActionFailure):
                raise ServiceValidationError(result.reason)

    if not hass.services.has_service(DOMAIN, "refresh"):
        hass.services.async_register(DOMAIN, "refresh", _handle_refresh)
    if not hass.services.has_service(DOMAIN, "create_assistant"):
        hass.services.async_register(
            DOMAIN, "create_assistant", _handle_create_assistant, schema=CREATE_ASSISTANT_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, "delete_assistant"):
        hass.services.async_register(
            DOMAIN, "delete_assistant", _handle_delete_assistant, schema=DELETE_ASSISTANT_SCHEMA
        )

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "refresh")
            hass.services.async_remove(DOMAIN, "create_assistant")
            hass.services.async_remove(DOMAIN, "delete_assistant")
    return unloaded
