from __future__ import annotations

from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SendMessageFailure, SendMessageSuccess
from .const import DOMAIN
from .coordinator import KinwardDataUpdateCoordinator
from .entity import KinwardEntity

TRANSPORT_ERROR_MESSAGE = "Kinward could not be reached to process that request."


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: KinwardDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KinwardConversationEntity(coordinator)])


class KinwardConversationEntity(KinwardEntity, ConversationEntity):
    """conversation.kinward - resolves the caller's HA user to a Kinward profile per request.

    An unmapped HA user (epics.md Story 2.1's fail-closed requirement) gets a
    truthful denial, never a fallback to household-shared or another person's
    context. Since no model provider exists in this deployment yet, a mapped
    request always gets the backend's truthful "no model configured" capability
    report rather than a real generated reply (epics.md Story 2.2).
    """

    _attr_name = None

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-conversation"

    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    @property
    def available(self) -> bool:
        return True

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        response = intent.IntentResponse(language=user_input.language)
        result = await self.coordinator.client.async_send_conversation_message(
            ha_user_id=user_input.context.user_id or "",
            text=user_input.text,
            conversation_id=user_input.conversation_id,
            language=user_input.language,
        )

        if isinstance(result, SendMessageFailure):
            response.async_set_speech(TRANSPORT_ERROR_MESSAGE)
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        assert isinstance(result, SendMessageSuccess)
        response.async_set_speech(result.response_text)
        return ConversationResult(
            response=response,
            conversation_id=result.conversation_id,
            continue_conversation=result.mapped and result.outcome == "completed",
        )
