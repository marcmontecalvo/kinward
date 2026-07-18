from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AssistantPolicy,
    AssistantPolicyFailure,
    ContextFailure,
    ContextSuccess,
    KinwardApiClient,
    ProviderSettings,
    ProviderSettingsFailure,
    ResourceLabel,
    ResourceLabelFailure,
    ToolPolicy,
    ToolPolicyFailure,
)
from .const import (
    CONF_BASE_URL,
    CONF_HONCHO_URL,
    CONF_KNOWLEDGE_BACKEND,
    CONF_LLM_WIKI_URL,
    CONF_MAX_ASSISTANTS_PER_PERSON,
    CONF_MEMORY_BACKEND,
    CONF_MODEL_API_KEY,
    CONF_MODEL_BASE_URL,
    CONF_MODEL_NAME,
    CONF_MODEL_PROVIDER,
    CONF_REQUIRE_ADMIN_APPROVAL_FOR_ASSISTANT_CREATION,
    CONF_RESOURCE_LABEL_ENTITY_ID,
    CONF_RESOURCE_LABEL_LABEL,
    CONF_TOKEN,
    DOMAIN,
    KNOWLEDGE_BACKENDS,
    MEMORY_BACKENDS,
    MODEL_PROVIDERS,
    NO_ASSISTANT_CAP,
    TOOL_POLICY_CAPABILITIES,
    TOOL_POLICY_DEFAULTS,
    TOOL_POLICY_VALUES,
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

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Entered automatically when the coordinator sees a rejected token
        (``ConfigEntryAuthFailed`` in coordinator.py) or from the entry's own
        "Reauthenticate" action. Only asks for a new token - base URL is
        unchanged, since a rotated backend token is the only credential that
        expires here.
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            session = async_get_clientsession(self.hass)
            client = KinwardApiClient(
                session, base_url=reauth_entry.data[CONF_BASE_URL], token=token
            )
            result = await client.async_fetch_context()

            if isinstance(result, ContextSuccess):
                if result.household_id != reauth_entry.unique_id:
                    return self.async_abort(reason="wrong_household")
                return self.async_update_reload_and_abort(
                    reauth_entry, data={**reauth_entry.data, CONF_TOKEN: token}
                )

            if isinstance(result, ContextFailure):
                errors["base"] = result.error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"base_url": reauth_entry.data[CONF_BASE_URL]},
        )


class KinwardOptionsFlowHandler(OptionsFlow):
    """Lets an admin change what LLM provider and which of the two memory systems
    (Honcho, llm_wiki) this Kinward household talks to, the household's policy for
    creating additional personal assistants, per-capability Home Assistant write
    permissions (Story 7.3), and household-language entity label overrides
    (Story 7.1) - without touching backend deployment config. All of it lives
    server-side; this flow only reads/writes it through the backend's admin API.
    """

    def _client(self) -> KinwardApiClient:
        entry = self.config_entry
        session = async_get_clientsession(self.hass)
        return KinwardApiClient(
            session, base_url=entry.data[CONF_BASE_URL], token=entry.data[CONF_TOKEN]
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["provider_settings", "tool_policy", "resource_labels"],
        )

    async def async_step_provider_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        client = self._client()

        if user_input is not None:
            provider_result = await client.async_update_provider_settings(
                model_provider=user_input[CONF_MODEL_PROVIDER],
                model_base_url=user_input.get(CONF_MODEL_BASE_URL, ""),
                model_name=user_input.get(CONF_MODEL_NAME, ""),
                model_api_key=user_input.get(CONF_MODEL_API_KEY) or None,
                memory_backend=user_input[CONF_MEMORY_BACKEND],
                honcho_url=user_input.get(CONF_HONCHO_URL, ""),
                knowledge_backend=user_input[CONF_KNOWLEDGE_BACKEND],
                llm_wiki_url=user_input.get(CONF_LLM_WIKI_URL, ""),
            )
            max_assistants = user_input[CONF_MAX_ASSISTANTS_PER_PERSON]
            policy_result = await client.async_update_assistant_policy(
                max_assistants_per_person=(
                    None if max_assistants == NO_ASSISTANT_CAP else max_assistants
                ),
                require_admin_approval_for_creation=user_input[
                    CONF_REQUIRE_ADMIN_APPROVAL_FOR_ASSISTANT_CREATION
                ],
            )
            if isinstance(provider_result, ProviderSettingsFailure):
                errors["base"] = provider_result.error
            elif isinstance(policy_result, AssistantPolicyFailure):
                errors["base"] = policy_result.error
            else:
                return self.async_create_entry(title="", data={})

        current = await client.async_fetch_provider_settings()
        defaults = current if isinstance(current, ProviderSettings) else None
        current_policy = await client.async_fetch_assistant_policy()
        policy_defaults = current_policy if isinstance(current_policy, AssistantPolicy) else None

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
                vol.Required(
                    CONF_MAX_ASSISTANTS_PER_PERSON,
                    default=(
                        (policy_defaults.max_assistants_per_person or NO_ASSISTANT_CAP)
                        if policy_defaults
                        else NO_ASSISTANT_CAP
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, step=1, mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_REQUIRE_ADMIN_APPROVAL_FOR_ASSISTANT_CREATION,
                    default=(
                        policy_defaults.require_admin_approval_for_creation
                        if policy_defaults
                        else False
                    ),
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="provider_settings", data_schema=schema, errors=errors)

    async def async_step_tool_policy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Story 7.3's ``HomeAssistantToolPolicyRecord`` - per-capability ``allow``/

        ``approval_required``/``deny`` for the five HA write capabilities in
        ``CAPABILITY_SERVICE_ALLOWLIST``. Previously callable via the REST contract
        only; this is that contract's first options-flow surface.
        """
        errors: dict[str, str] = {}
        client = self._client()

        if user_input is not None:
            result = await client.async_update_tool_policy(
                permissions={
                    capability: user_input[capability] for capability in TOOL_POLICY_CAPABILITIES
                }
            )
            if isinstance(result, ToolPolicyFailure):
                errors["base"] = result.error
            else:
                return self.async_create_entry(title="", data={})

        current = await client.async_fetch_tool_policy()
        defaults = current.permissions if isinstance(current, ToolPolicy) else {}

        schema = vol.Schema(
            {
                vol.Required(
                    capability, default=defaults.get(capability, TOOL_POLICY_DEFAULTS[capability])
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TOOL_POLICY_VALUES, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
                for capability in TOOL_POLICY_CAPABILITIES
            }
        )
        return self.async_show_form(step_id="tool_policy", data_schema=schema, errors=errors)

    async def async_step_resource_labels(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Story 7.1's ``home_assistant_resource_labels`` override table - one

        entity/label pair per submission (blank label deletes the override, falling
        back to HA's own ``friendly_name`` then the raw entity id). Previously
        callable via the REST contract only; this is that contract's first
        options-flow surface. Existing overrides are listed in the form
        description since there's no HA options-flow list editor to edit them
        inline.
        """
        errors: dict[str, str] = {}
        client = self._client()

        if user_input is not None:
            entity_id = user_input[CONF_RESOURCE_LABEL_ENTITY_ID]
            label = user_input.get(CONF_RESOURCE_LABEL_LABEL, "").strip()
            label_result: ResourceLabel | ResourceLabelFailure | None
            if label:
                label_result = await client.async_set_resource_label(
                    entity_id=entity_id, label=label
                )
            else:
                label_result = await client.async_delete_resource_label(entity_id=entity_id)
            if isinstance(label_result, ResourceLabelFailure):
                errors["base"] = label_result.error
            else:
                return self.async_create_entry(title="", data={})

        current = await client.async_list_resource_labels()
        existing = current if isinstance(current, list) else []
        current_labels = (
            "\n".join(f"- {item.entity_id}: {item.label}" for item in existing)
            if existing
            else "(none set)"
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_RESOURCE_LABEL_ENTITY_ID): selector.EntitySelector(),
                vol.Optional(CONF_RESOURCE_LABEL_LABEL, default=""): selector.TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="resource_labels",
            data_schema=schema,
            errors=errors,
            description_placeholders={"current_labels": current_labels},
        )
