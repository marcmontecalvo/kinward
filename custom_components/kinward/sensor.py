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
