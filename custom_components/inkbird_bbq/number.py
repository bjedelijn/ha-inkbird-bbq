"""Experimental number controls for INKBIRD BBQ hardware validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InkbirdBbqConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL_INT_14_BW, MODEL_ISC_027BW
from .coordinator import (
    InkbirdBbqCoordinator,
    Int14bwCoordinator,
    Isc027bwCoordinator,
)


@dataclass(frozen=True, kw_only=True)
class InkbirdNumberDescription(NumberEntityDescription):
    """Describe an experimental INKBIRD BBQ number control."""

    data_key: str


INT14BW_NUMBERS = (
    InkbirdNumberDescription(
        key="display_brightness_control",
        translation_key="display_brightness_control",
        data_key="display_brightness",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
    ),
    *(
        InkbirdNumberDescription(
            key=f"probe_{probe}_target_control",
            translation_key=f"probe_{probe}_target_control",
            data_key=f"probe_{probe}_target",
            native_min_value=0,
            native_max_value=100,
            native_step=1,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        for probe in range(1, 5)
    ),
)

ISC027BW_NUMBERS = (
    InkbirdNumberDescription(
        key="pit_target_control",
        translation_key="pit_target_control",
        data_key="pit_target",
        native_min_value=20,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
    InkbirdNumberDescription(
        key="pit_high_alarm_control",
        translation_key="pit_high_alarm_control",
        data_key="pit_high_alarm",
        native_min_value=20,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
    InkbirdNumberDescription(
        key="pit_low_alarm_control",
        translation_key="pit_low_alarm_control",
        data_key="pit_low_alarm",
        native_min_value=20,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
    *(
        InkbirdNumberDescription(
            key=f"{key}_calibration_control",
            translation_key=f"{key}_calibration_control",
            data_key=f"{key}_calibration",
            native_min_value=-12.8,
            native_max_value=12.7,
            native_step=0.1,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        for key in ("pit", "probe_1", "probe_2", "probe_3")
    ),
    *(
        InkbirdNumberDescription(
            key=f"probe_{probe}_alarm_control",
            translation_key=f"probe_{probe}_alarm_control",
            data_key=f"meat_probe_{probe}_alarm",
            native_min_value=20,
            native_max_value=300,
            native_step=1,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        for probe in range(1, 4)
    ),
)


async def async_setup_entry(
    hass: Any,
    entry: InkbirdBbqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up experimental number controls."""
    coordinator = entry.runtime_data
    descriptions = (
        ISC027BW_NUMBERS
        if coordinator.model == MODEL_ISC_027BW
        else INT14BW_NUMBERS
        if coordinator.model == MODEL_INT_14_BW
        else ()
    )
    async_add_entities(
        InkbirdBbqNumber(coordinator, description) for description in descriptions
    )


class InkbirdBbqNumber(CoordinatorEntity[InkbirdBbqCoordinator], NumberEntity):
    """Experimental INKBIRD BBQ number control."""

    entity_description: InkbirdNumberDescription
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: InkbirdBbqCoordinator,
        description: InkbirdNumberDescription,
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
        return bool(self.coordinator.data.get("available"))

    @property
    def _is_int14_target(self) -> bool:
        return (
            isinstance(self.coordinator, Int14bwCoordinator)
            and self.entity_description.key.startswith("probe_")
            and self.entity_description.key.endswith("_target_control")
        )

    @property
    def _is_isc_temperature_control(self) -> bool:
        return isinstance(self.coordinator, Isc027bwCoordinator) and (
            self.entity_description.key == "pit_target_control"
            or self.entity_description.key in {
                "pit_high_alarm_control",
                "pit_low_alarm_control",
            }
            or self.entity_description.key.endswith("_alarm_control")
            or self.entity_description.key.endswith("_calibration_control")
        )

    @property
    def _is_isc_calibration(self) -> bool:
        return (
            isinstance(self.coordinator, Isc027bwCoordinator)
            and self.entity_description.key.endswith("_calibration_control")
        )

    @property
    def _uses_fahrenheit(self) -> bool:
        return (
            self._is_int14_target or self._is_isc_temperature_control
        ) and self.coordinator.data.get("temperature_unit") == "F"

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self._is_int14_target or self._is_isc_temperature_control:
            return (
                UnitOfTemperature.FAHRENHEIT
                if self._uses_fahrenheit
                else UnitOfTemperature.CELSIUS
            )
        return self.entity_description.native_unit_of_measurement

    @property
    def native_min_value(self) -> float:
        if self._is_int14_target:
            return 32.0 if self._uses_fahrenheit else 0.0
        if self._is_isc_temperature_control and not self._is_isc_calibration:
            return 68.0 if self._uses_fahrenheit else 20.0
        return self.entity_description.native_min_value or 0.0

    @property
    def native_max_value(self) -> float:
        if self._is_int14_target:
            return 212.0 if self._uses_fahrenheit else 100.0
        if self._is_isc_temperature_control and not self._is_isc_calibration:
            return 572.0 if self._uses_fahrenheit else 300.0
        return self.entity_description.native_max_value or 100.0

    @property
    def native_step(self) -> float | None:
        if self._is_int14_target:
            return 1.0
        return self.entity_description.native_step

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.data_key)
        if not isinstance(value, int | float):
            return None
        if self._uses_fahrenheit and not self._is_isc_calibration:
            return round(float(value) * 9.0 / 5.0 + 32.0, 1)
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        key = self.entity_description.key

        if isinstance(self.coordinator, Int14bwCoordinator):
            if key == "display_brightness_control":
                await self.coordinator.async_set_display_brightness(round(value))
                return
            if key.startswith("probe_") and key.endswith("_target_control"):
                probe = int(key.split("_")[1])
                target_celsius = (
                    (value - 32.0) * 5.0 / 9.0
                    if self._uses_fahrenheit
                    else value
                )
                await self.coordinator.async_set_probe_target(
                    probe,
                    target_celsius,
                )
                return
        if isinstance(self.coordinator, Isc027bwCoordinator):
            target_value = (
                (value - 32.0) * 5.0 / 9.0
                if self._uses_fahrenheit and not self._is_isc_calibration
                else value
            )
            if key == "pit_target_control":
                await self.coordinator.async_set_pit_target(target_value)
                return
            if key == "pit_high_alarm_control":
                await self.coordinator.async_set_pit_high_alarm(target_value)
                return
            if key == "pit_low_alarm_control":
                await self.coordinator.async_set_pit_low_alarm(target_value)
                return
            if key.endswith("_calibration_control"):
                calibration_key = key.removesuffix("_calibration_control")
                await self.coordinator.async_set_calibration(calibration_key, value)
                return
            if key.startswith("probe_") and key.endswith("_alarm_control"):
                probe = int(key.split("_")[1])
                await self.coordinator.async_set_probe_alarm(probe, target_value)
                return

        raise RuntimeError(f"Unsupported experimental number control: {key}")

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
