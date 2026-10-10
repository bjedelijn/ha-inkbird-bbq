"""Binary sensor platform for INKBIRD BBQ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InkbirdBbqConfigEntry
from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_INT_14_BW,
    MODEL_ISC_027BW,
    MODEL_TNT_11_B,
)

if TYPE_CHECKING:
    from .coordinator import InkbirdBbqCoordinator


@dataclass(frozen=True, kw_only=True)
class InkbirdBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an INKBIRD BBQ binary sensor."""

    data_key: str


ISC027BW_BINARY_SENSORS = (
    InkbirdBinarySensorDescription(
        key="fan_on",
        translation_key="fan_on",
        data_key="fan_on",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
)

INT14BW_BINARY_SENSORS = tuple(
    InkbirdBinarySensorDescription(
        key=f"probe_{probe}_docked",
        translation_key=f"probe_{probe}_docked",
        data_key=f"probe_{probe}_docked",
        device_class=BinarySensorDeviceClass.PLUG,
    )
    for probe in range(1, 5)
)

TNT11B_BINARY_SENSORS = (
    InkbirdBinarySensorDescription(
        key="charging",
        translation_key="charging",
        data_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
)


async def async_setup_entry(
    hass: Any,
    entry: InkbirdBbqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up INKBIRD BBQ binary sensors."""
    coordinator = entry.runtime_data

    if coordinator.model == MODEL_ISC_027BW:
        descriptions = ISC027BW_BINARY_SENSORS
    elif coordinator.model == MODEL_INT_14_BW:
        descriptions = INT14BW_BINARY_SENSORS
    elif coordinator.model == MODEL_TNT_11_B:
        descriptions = TNT11B_BINARY_SENSORS
    else:
        descriptions = ()

    async_add_entities(
        InkbirdBbqBinarySensor(coordinator, description)
        for description in descriptions
    )


class InkbirdBbqBinarySensor(
    CoordinatorEntity[Any],
    BinarySensorEntity,
):
    """Representation of an INKBIRD BBQ binary sensor."""

    entity_description: InkbirdBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InkbirdBbqCoordinator,
        description: InkbirdBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.address}_{description.key}".lower().replace(":", "")
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            manufacturer=MANUFACTURER,
            model=coordinator.model,
            name=f"INKBIRD {coordinator.model}",
        )

    @property
    def available(self) -> bool:
        """Return device availability."""
        return bool(self.coordinator.data.get("available"))

    @property
    def is_on(self) -> bool | None:
        """Return the latest binary state."""
        value = self.coordinator.data.get(self.entity_description.data_key)
        return bool(value) if value is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle pushed Bluetooth updates."""
        self.async_write_ha_state()
