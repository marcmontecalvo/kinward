from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KinwardDataUpdateCoordinator
from .entity import KinwardEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: KinwardDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KinwardBackendConnectivitySensor(coordinator)])


class KinwardBackendConnectivitySensor(KinwardEntity, BinarySensorEntity):
    """Reports whether the last poll of the Kinward backend succeeded.

    This entity is intentionally always ``available`` - it *is* the availability
    signal, so it must not itself disappear when the backend is unreachable.
    """

    _attr_translation_key = "backend"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.household_id}-backend"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success
