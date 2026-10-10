"""Experimental switch controls for INKBIRD BBQ hardware validation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InkbirdBbqConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL_ISC_027BW
from .coordinator import InkbirdBbqCoordinator, Isc027bwCoordinator


async def async_setup_entry(
    hass: Any,
    entry: InkbirdBbqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up experimental switches."""
    coordinator = entry.runtime_data

    if coordinator.model == MODEL_ISC_027BW:
        async_add_entities(
            [
                InkbirdExperimentalSwitch(coordinator, "fan_control"),
                InkbirdExperimentalSwitch(coordinator, "lid_reminder_control"),
                InkbirdExperimentalSwitch(coordinator, "device_sound_control"),
            ]
        )


class InkbirdExperimentalSwitch(
    CoordinatorEntity[InkbirdBbqCoordinator],
    SwitchEntity,
):
    """Experimental INKBIRD BBQ switch."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: InkbirdBbqCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = (
            f"{coordinator.address}_{key}".lower().replace(":", "")
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
    def is_on(self) -> bool | None:
        data_key = {
            "fan_control": "fan_on",
            "lid_reminder_control": "lid_reminder",
            "device_sound_control": "device_sound",
        }.get(self._key)
        if data_key is None:
            return None
        value = self.coordinator.data.get(data_key)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self._key == "fan_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_fan_on(True)
            return
        if self._key == "lid_reminder_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_lid_reminder(True)
            return
        if self._key == "device_sound_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_device_sound(True)
            return
        raise RuntimeError(f"Unsupported experimental switch: {self._key}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._key == "fan_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_fan_on(False)
            return
        if self._key == "lid_reminder_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_lid_reminder(False)
            return
        if self._key == "device_sound_control" and isinstance(
            self.coordinator, Isc027bwCoordinator
        ):
            await self.coordinator.async_set_device_sound(False)
            return
        raise RuntimeError(f"Unsupported experimental switch: {self._key}")

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
