from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .coordinator import KinwardDataUpdateCoordinator
from .entity import KinwardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: KinwardDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            KinwardHouseholdStatusSensor(coordinator),
            KinwardBriefingSensor(coordinator),
            KinwardAttentionSensor(coordinator),
            KinwardNextEventSensor(coordinator),
            KinwardLastRefreshSensor(coordinator),
            KinwardPeopleSensor(coordinator),
            KinwardPetsSensor(coordinator),
            KinwardPendingApprovalsSensor(coordinator),
            KinwardAssistantsSensor(coordinator),
            KinwardConnectedAccountsSensor(coordinator),
        ]
    )


class KinwardHouseholdStatusSensor(KinwardEntity, SensorEntity):
    _attr_translation_key = "household_status"

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-household-status"

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        return f"{data.adult_count} adults, {data.child_count} children"

    @property
    def extra_state_attributes(self) -> dict[str, int] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {"adult_count": data.adult_count, "child_count": data.child_count}


class KinwardBriefingSensor(KinwardEntity, SensorEntity):
    _attr_translation_key = "briefing"

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-briefing"

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data
        return data.briefing.summary if data else None

    @property
    def extra_state_attributes(self) -> dict[str, str | None] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {"capability_state": data.briefing.state, "reason": data.briefing.reason}


class KinwardAttentionSensor(KinwardEntity, SensorEntity):
    """Calendar attention items requiring notice or action (Epic 5 Story 5.3/5.5).

    ``items`` carries every currently active/acknowledged/recently-resolved item so
    the dashboard can distinguish them, matching the bounded-detail-in-attributes
    precedent already used by ``KinwardPeopleSensor``/``KinwardPendingApprovalsSensor``
    rather than a large nested payload.
    """

    _attr_translation_key = "attention"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-attention"

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        return data.attention.count if data else None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {
            "capability_state": data.attention.state,
            "reason": data.attention.reason,
            "items": [
                {
                    "id": item.id,
                    "change_type": item.change_type,
                    "state": item.state,
                    "summary": item.summary,
                    "entity_id": item.entity_id,
                    "event_starts_at": item.event_starts_at,
                }
                for item in self.coordinator.attention_items
            ],
        }


class KinwardNextEventSensor(KinwardEntity, SensorEntity):
    _attr_translation_key = "next_event"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-next-event"

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        if data is None or not data.next_event.starts_at:
            return None
        return dt_util.parse_datetime(data.next_event.starts_at)

    @property
    def extra_state_attributes(self) -> dict[str, str | None] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {
            "capability_state": data.next_event.state,
            "reason": data.next_event.reason,
            "summary": data.next_event.summary,
        }


class KinwardPeopleSensor(KinwardEntity, SensorEntity):
    """Every synced person and the Kinward role (admin/member) they currently hold.

    Role is derived live from HA's own admin flag on every sync pass - there is no
    Kinward-side admin designation to look up separately (see coordinator/people_sync).
    """

    _attr_name = "People"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-people"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.people)

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, str | None]]]:
        return {
            "people": [
                {
                    "id": person.id,
                    "display_name": person.display_name,
                    "role": person.role,
                    "ha_person_id": person.ha_person_id,
                    "ha_user_id": person.ha_user_id,
                }
                for person in self.coordinator.people
            ]
        }


class KinwardPetsSensor(KinwardEntity, SensorEntity):
    """Every household-shared pet profile currently on record."""

    _attr_name = "Pets"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-pets"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.pets)

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, object]]]:
        return {
            "pets": [
                {
                    "id": pet.id,
                    "display_name": pet.display_name,
                    "species": pet.species,
                    "shared_facts": pet.shared_facts,
                }
                for pet in self.coordinator.pets
            ]
        }


class KinwardAssistantsSensor(KinwardEntity, SensorEntity):
    """Every household assistant's public visual identity (Epic 3 Story 3.7) - the

    data source for a Lovelace card (Story 10.5). Deliberately public-only fields
    (name, visual pack, current stage, accent) - never ``personality``, which stays
    private per-owner and must never enter shared HA entity state (cross-cutting
    architecture rule 6). Mirrors ``KinwardPeopleSensor``'s "role/display_name are
    fine to broadcast, private content is not" precedent.
    """

    _attr_name = "Assistants"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-assistants"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.assistant_identities)

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, object]]]:
        return {
            "assistants": [
                {
                    "id": assistant.id,
                    "name": assistant.name,
                    "owner_person_id": assistant.owner_person_id,
                    "visual_pack_id": assistant.visual_pack_id,
                    "visual_stage": assistant.visual_stage,
                    "visual_stage_icon": assistant.visual_stage_icon,
                    "visual_stage_preview_image": assistant.visual_stage_preview_image,
                    "accent": assistant.accent,
                }
                for assistant in self.coordinator.assistant_identities
            ]
        }


class KinwardPendingApprovalsSensor(KinwardEntity, SensorEntity):
    """Meaningful actions currently awaiting admin approval (Epic 6; ADR-002 sec. 5).

    Any current household admin may resolve one via the ``kinward.approve_action``/
    ``kinward.deny_action`` actions - there is no per-resource owner to notify for
    the HA device-control case this covers (see ``application/pending_actions.py``).
    """

    _attr_name = "Pending approvals"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-pending-approvals"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.pending_actions)

    @property
    def extra_state_attributes(self) -> dict[str, list[dict[str, object]]]:
        return {
            "pending_actions": [
                {
                    "id": action.id,
                    "action": action.action,
                    "explanation": action.explanation,
                    "domain": action.domain,
                    "service": action.service,
                    "entity_id": action.entity_id,
                    "created_at": action.created_at,
                    "expires_at": action.expires_at,
                }
                for action in self.coordinator.pending_actions
            ]
        }


class KinwardConnectedAccountsSensor(KinwardEntity, SensorEntity):
    """Connected Google/Microsoft calendar accounts (Epic 5 v1 roadmap item 1/2) - off-script
    per product owner: connecting an account itself happens on a Kinward-served setup page
    (``setup_url``), not through this sensor or any HA service call, since only a real browser
    redirect to the provider's consent screen can complete OAuth. This sensor exists so that
    page is discoverable from Home Assistant, and so connection status - handy when a token
    needs reauthorization - is visible without leaving HA.
    """

    _attr_name = "Connected accounts"
    _attr_icon = "mdi:calendar-sync"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-connected-accounts"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.connected_accounts)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "setup_url": f"{self.coordinator.client.base_url}/setup/accounts",
            "needs_reauthorization": sum(
                1
                for account in self.coordinator.connected_accounts
                if account.status == "reauthorization_required"
            ),
            "accounts": [
                {
                    "id": account.id,
                    "provider": account.provider,
                    "provider_account_email": account.provider_account_email,
                    "status": account.status,
                    "owner_display_name": account.owner_display_name,
                    "last_synced_at": account.last_synced_at,
                }
                for account in self.coordinator.connected_accounts
            ],
        }


class KinwardLastRefreshSensor(KinwardEntity, SensorEntity):
    """The last time the coordinator's poll of the Kinward backend succeeded."""

    _attr_translation_key = "last_refresh"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-last-refresh"

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_success_at
