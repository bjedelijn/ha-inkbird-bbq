"""Sensor platform for INKBIRD BBQ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
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
from .coordinator import InkbirdBbqCoordinator


@dataclass(frozen=True, kw_only=True)
class InkbirdSensorDescription(SensorEntityDescription):
    """Describe an INKBIRD BBQ sensor."""

    data_key: str


ISC027BW_SENSORS: tuple[InkbirdSensorDescription, ...] = (
    InkbirdSensorDescription(
        key="pit_temperature",
        translation_key="pit_temperature",
        data_key="pit_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="meat_probe_1",
        translation_key="meat_probe_1",
        data_key="meat_probe_1",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="meat_probe_2",
        translation_key="meat_probe_2",
        data_key="meat_probe_2",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="meat_probe_3",
        translation_key="meat_probe_3",
        data_key="meat_probe_3",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="fan_output",
        translation_key="fan_output",
        data_key="fan_output",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="pit_target",
        translation_key="pit_target",
        data_key="pit_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    InkbirdSensorDescription(
        key="meat_probe_1_alarm",
        translation_key="meat_probe_1_alarm",
        data_key="meat_probe_1_alarm",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    InkbirdSensorDescription(
        key="meat_probe_2_alarm",
        translation_key="meat_probe_2_alarm",
        data_key="meat_probe_2_alarm",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    InkbirdSensorDescription(
        key="meat_probe_3_alarm",
        translation_key="meat_probe_3_alarm",
        data_key="meat_probe_3_alarm",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
)

TNT11B_SENSORS: tuple[InkbirdSensorDescription, ...] = (
    InkbirdSensorDescription(
        key="probe_temperature",
        translation_key="probe_temperature",
        data_key="probe_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    InkbirdSensorDescription(
        key="ambient_temperature",
        translation_key="ambient_temperature",
        data_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

INT14BW_SENSORS: tuple[InkbirdSensorDescription, ...] = tuple(
    [
        InkbirdSensorDescription(
            key=f"probe_{probe}_core",
            translation_key=f"probe_{probe}_core",
            data_key=f"probe_{probe}_core",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        )
        for probe in range(1, 5)
    ]
    + [
        InkbirdSensorDescription(
            key=f"probe_{probe}_ambient",
            translation_key=f"probe_{probe}_ambient",
            data_key=f"probe_{probe}_ambient",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        )
        for probe in range(1, 5)
    ]
    + [
        InkbirdSensorDescription(
            key="base_battery",
            translation_key="base_battery",
            data_key="base_battery",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )
    ]
    + [
        InkbirdSensorDescription(
            key=f"probe_{probe}_battery",
            translation_key=f"probe_{probe}_battery",
            data_key=f"probe_{probe}_battery",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )
        for probe in range(1, 5)
    ]
)


async def async_setup_entry(
    hass: Any,
    entry: InkbirdBbqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up read-only INKBIRD BBQ sensors."""
    coordinator = entry.runtime_data

    if coordinator.model == MODEL_ISC_027BW:
        descriptions = ISC027BW_SENSORS
    elif coordinator.model == MODEL_INT_14_BW:
        descriptions = INT14BW_SENSORS
    elif coordinator.model == MODEL_TNT_11_B:
        descriptions = TNT11B_SENSORS
    else:
        descriptions = ()

    async_add_entities(
        InkbirdBbqSensor(coordinator, description)
        for description in descriptions
    )


class InkbirdBbqSensor(
    CoordinatorEntity[InkbirdBbqCoordinator],
    SensorEntity,
):
    """Representation of an INKBIRD BBQ read-only sensor."""

    entity_description: InkbirdSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InkbirdBbqCoordinator,
        description: InkbirdSensorDescription,
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
    def native_value(self) -> Any:
        """Return the latest decoded value."""
        return self.coordinator.data.get(self.entity_description.data_key)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle pushed Bluetooth updates."""
        self.async_write_ha_state()
