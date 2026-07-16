from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ContextFailure, ContextSuccess, KinwardApiClient
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
        ),
        vol.Required(CONF_TOKEN): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class KinwardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Connects to a Kinward backend.

    Kinward has no identity system of its own - people are synced from Home
    Assistant's own ``person.*`` entities on every coordinator poll (see
    coordinator.py), and whoever is a Home Assistant administrator is a
    Kinward administrator too (any number of people can hold that role at
    once - it's read from HA's own admin flag, never designated here).
    Nothing further is asked at setup.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            token = user_input[CONF_TOKEN]
            session = async_get_clientsession(self.hass)
            client = KinwardApiClient(session, base_url=base_url, token=token)
            result = await client.async_fetch_context()

            if isinstance(result, ContextSuccess):
                await self.async_set_unique_id(result.household_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=result.household_name,
                    data={CONF_BASE_URL: base_url, CONF_TOKEN: token},
                )

            if isinstance(result, ContextFailure):
                errors["base"] = result.error

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
