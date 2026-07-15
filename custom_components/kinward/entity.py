from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KinwardDataUpdateCoordinator


class KinwardEntity(CoordinatorEntity[KinwardDataUpdateCoordinator]):
    """Base for entities grouped under the single Kinward device for this household."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KinwardDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.household_id)},
            name="Kinward",
            manufacturer="Kinward",
        )
