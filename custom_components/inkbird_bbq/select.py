"""Experimental select controls for INKBIRD BBQ hardware validation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
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


async def async_setup_entry(
    hass: Any,
    entry: InkbirdBbqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the temperature-unit control."""
    coordinator = entry.runtime_data
    if coordinator.model in (MODEL_INT_14_BW, MODEL_ISC_027BW):
        async_add_entities([InkbirdTemperatureUnitSelect(coordinator)])


class InkbirdTemperatureUnitSelect(
    CoordinatorEntity[InkbirdBbqCoordinator],
    SelectEntity,
):
    """Experimental C/F selector for supported INKBIRD devices."""

    _attr_has_entity_name = True
    _attr_translation_key = "temperature_unit_control"
    _attr_options = ["Celsius", "Fahrenheit"]
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: InkbirdBbqCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.address}_temperature_unit_control".lower().replace(":", "")
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
    def current_option(self) -> str | None:
        value = self.coordinator.data.get("temperature_unit")
        if value == "C":
            return "Celsius"
        if value == "F":
            return "Fahrenheit"
        return None

    async def async_select_option(self, option: str) -> None:
        unit = "C" if option == "Celsius" else "F"
        if isinstance(self.coordinator, (Int14bwCoordinator, Isc027bwCoordinator)):
            await self.coordinator.async_set_temperature_unit(unit)
            return
        raise RuntimeError("Temperature-unit control is not supported for this model")

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
