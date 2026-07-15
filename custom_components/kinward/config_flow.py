from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ContextFailure,
    ContextSuccess,
    HaUserMapping,
    KinwardApiClient,
    MappingsSuccess,
    PeopleSuccess,
)
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

UNMAPPED = "__unmapped__"


class KinwardConfigFlow(ConfigFlow, domain=DOMAIN):
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> KinwardOptionsFlowHandler:
        return KinwardOptionsFlowHandler()


class KinwardOptionsFlowHandler(OptionsFlow):
    """Maps Home Assistant users to account-bearing Kinward profiles.

    The mapping is authoritative on the Kinward backend (see AD-05's
    AccessContext) - this form only edits it through the existing service
    token; nothing person-identifying is stored in HA's own config-entry data.

    Home Assistant users are presented one at a time (rather than as one form
    with a dynamic field per user) so each step's translated description can
    show that user's real name via a placeholder - a single dynamic-keyed form
    would only be able to show each field's raw HA user ID as its label.
    """

    def __init__(self) -> None:
        self._client: KinwardApiClient | None = None
        self._people: list[selector.SelectOptionDict] = []
        self._current: dict[str, str] = {}
        self._ha_users: list[Any] = []
        self._index = 0
        self._changes: dict[str, str | None] = {}

    async def async_step_init(self, _user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        client = KinwardApiClient(
            async_get_clientsession(self.hass),
            base_url=self.config_entry.data[CONF_BASE_URL],
            token=self.config_entry.data[CONF_TOKEN],
        )
        people_result = await client.async_fetch_people()
        mappings_result = await client.async_fetch_ha_user_mappings()
        if not isinstance(people_result, PeopleSuccess) or not isinstance(
            mappings_result, MappingsSuccess
        ):
            return self.async_abort(reason="cannot_connect")
        if not people_result.people:
            return self.async_abort(reason="no_account_bearing_people")

        ha_users = [
            user
            for user in await self.hass.auth.async_get_users()
            if not user.system_generated and user.is_active
        ]
        if not ha_users:
            return self.async_abort(reason="no_ha_users")

        self._client = client
        self._people = [
            selector.SelectOptionDict(value=person.id, label=person.display_name)
            for person in people_result.people
        ] + [selector.SelectOptionDict(value=UNMAPPED, label="Not mapped")]
        self._current = {mapping.ha_user_id: mapping.person_id for mapping in mappings_result.mappings}
        self._ha_users = ha_users
        self._index = 0
        self._changes = {}
        return await self._async_step_for_current_user()

    async def _async_step_for_current_user(self) -> ConfigFlowResult:
        if self._index >= len(self._ha_users):
            return await self._async_apply_changes()

        ha_user = self._ha_users[self._index]
        schema = vol.Schema(
            {
                vol.Optional(
                    "person_id", default=self._current.get(ha_user.id, UNMAPPED)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._people, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="map_user",
            data_schema=schema,
            description_placeholders={"ha_user_name": ha_user.name or ha_user.id},
        )

    async def async_step_map_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return await self._async_step_for_current_user()
        ha_user = self._ha_users[self._index]
        selected = user_input["person_id"]
        self._changes[ha_user.id] = None if selected == UNMAPPED else selected
        self._index += 1
        return await self._async_step_for_current_user()

    async def _async_apply_changes(self) -> ConfigFlowResult:
        assert self._client is not None
        to_upsert = [
            HaUserMapping(ha_user_id=ha_user_id, person_id=person_id)
            for ha_user_id, person_id in self._changes.items()
            if person_id is not None and person_id != self._current.get(ha_user_id)
        ]
        to_remove = [
            ha_user_id
            for ha_user_id, person_id in self._changes.items()
            if person_id is None and ha_user_id in self._current
        ]
        if to_upsert:
            upsert_result = await self._client.async_put_ha_user_mappings(to_upsert)
            if not isinstance(upsert_result, MappingsSuccess):
                return self.async_abort(reason="cannot_connect")
        for ha_user_id in to_remove:
            await self._client.async_delete_ha_user_mapping(ha_user_id)
        return self.async_create_entry(title="", data={})
