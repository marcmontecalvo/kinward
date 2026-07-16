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
    def extra_state_attributes(self) -> dict[str, str | None] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {"capability_state": data.attention.state, "reason": data.attention.reason}


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
