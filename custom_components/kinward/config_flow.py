from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ContextFailure,
    ContextSuccess,
    KinwardApiClient,
    ProviderSettings,
    ProviderSettingsFailure,
)
from .const import (
    CONF_BASE_URL,
    CONF_HONCHO_URL,
    CONF_KNOWLEDGE_BACKEND,
    CONF_LLM_WIKI_URL,
    CONF_MEMORY_BACKEND,
    CONF_MODEL_API_KEY,
    CONF_MODEL_BASE_URL,
    CONF_MODEL_NAME,
    CONF_MODEL_PROVIDER,
    CONF_TOKEN,
    DOMAIN,
    KNOWLEDGE_BACKENDS,
    MEMORY_BACKENDS,
    MODEL_PROVIDERS,
)

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

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> KinwardOptionsFlowHandler:
        return KinwardOptionsFlowHandler()

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


class KinwardOptionsFlowHandler(OptionsFlow):
    """Lets an admin change what LLM provider and which of the two memory systems
    (Honcho, llm_wiki) this Kinward household talks to, without touching backend
    deployment config - settings live server-side and this flow only reads/writes
    them through the backend's admin API.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self.config_entry
        session = async_get_clientsession(self.hass)
        client = KinwardApiClient(
            session, base_url=entry.data[CONF_BASE_URL], token=entry.data[CONF_TOKEN]
        )

        if user_input is not None:
            result = await client.async_update_provider_settings(
                model_provider=user_input[CONF_MODEL_PROVIDER],
                model_base_url=user_input.get(CONF_MODEL_BASE_URL, ""),
                model_name=user_input.get(CONF_MODEL_NAME, ""),
                model_api_key=user_input.get(CONF_MODEL_API_KEY) or None,
                memory_backend=user_input[CONF_MEMORY_BACKEND],
                honcho_url=user_input.get(CONF_HONCHO_URL, ""),
                knowledge_backend=user_input[CONF_KNOWLEDGE_BACKEND],
                llm_wiki_url=user_input.get(CONF_LLM_WIKI_URL, ""),
            )
            if isinstance(result, ProviderSettingsFailure):
                errors["base"] = result.error
            else:
                return self.async_create_entry(title="", data={})

        current = await client.async_fetch_provider_settings()
        defaults = current if isinstance(current, ProviderSettings) else None

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MODEL_PROVIDER, default=defaults.model_provider if defaults else "none"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=MODEL_PROVIDERS, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    CONF_MODEL_BASE_URL, default=(defaults.model_base_url or "") if defaults else ""
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_MODEL_NAME, default=(defaults.model_name or "") if defaults else ""
                ): selector.TextSelector(),
                vol.Optional(CONF_MODEL_API_KEY, default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_MEMORY_BACKEND, default=defaults.memory_backend if defaults else "none"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=MEMORY_BACKENDS, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    CONF_HONCHO_URL, default=(defaults.honcho_url or "") if defaults else ""
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                ),
                vol.Required(
                    CONF_KNOWLEDGE_BACKEND, default=defaults.knowledge_backend if defaults else "none"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=KNOWLEDGE_BACKENDS, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    CONF_LLM_WIKI_URL, default=(defaults.llm_wiki_url or "") if defaults else ""
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
