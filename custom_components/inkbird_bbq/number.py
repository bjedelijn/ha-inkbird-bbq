"""Experimental number controls for INKBIRD BBQ hardware validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InkbirdBbqConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL_INT_14_BW, MODEL_ISC_027BW
from .coordinator import InkbirdBbqCoordinator, Int14bwCoordinator, Isc027bwCoordinator


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
    InkbirdNumberDescription(
        key="auto_sleep_control",
        translation_key="auto_sleep_control",
        data_key="auto_sleep_minutes",
        native_min_value=0,
        native_max_value=1092,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
)

ISC027BW_NUMBERS = (
    InkbirdNumberDescription(
        key="fan_setpoint_control",
        translation_key="fan_setpoint_control",
        data_key="fan_setpoint",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
    ),
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
    """Set up disabled-by-default experimental number controls."""
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
    _attr_entity_registry_enabled_default = False

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
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.data_key)
        return float(value) if isinstance(value, int | float) else None

    async def async_set_native_value(self, value: float) -> None:
        key = self.entity_description.key

        if isinstance(self.coordinator, Int14bwCoordinator):
            if key == "display_brightness_control":
                await self.coordinator.async_set_display_brightness(round(value))
                return
            if key == "auto_sleep_control":
                await self.coordinator.async_set_auto_sleep_minutes(round(value))
                return

        if isinstance(self.coordinator, Isc027bwCoordinator):
            if key == "fan_setpoint_control":
                await self.coordinator.async_set_fan_setpoint(round(value))
                return
            if key == "pit_target_control":
                await self.coordinator.async_set_pit_target(value)
                return
            if key.startswith("probe_") and key.endswith("_alarm_control"):
                probe = int(key.split("_")[1])
                await self.coordinator.async_set_probe_alarm(probe, value)
                return

        raise RuntimeError(f"Unsupported experimental number control: {key}")

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
