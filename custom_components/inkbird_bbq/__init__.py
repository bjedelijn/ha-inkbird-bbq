"""INKBIRD BBQ integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform

from .const import CONF_MODEL, MODEL_INT_14_BW

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import InkbirdBbqCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type InkbirdBbqConfigEntry = ConfigEntry["InkbirdBbqCoordinator"]

_DEPRECATED_INT14_ENTITY_SUFFIXES = {
    "_temperature_unit",
    "_display_brightness",
    "_auto_sleep_minutes",
    "_auto_sleep_control",
    "_wifi_control",
    "_wifi_enabled",
}


def _cleanup_deprecated_int14_entities(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> None:
    """Remove obsolete INT-14-BW entities left behind by development builds."""
    if entry.data.get(CONF_MODEL) != MODEL_INT_14_BW:
        return

    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if any(
            entity_entry.unique_id.endswith(suffix)
            for suffix in _DEPRECATED_INT14_ENTITY_SUFFIXES
        ):
            registry.async_remove(entity_entry.entity_id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> bool:
    """Set up INKBIRD BBQ from a config entry."""
    from homeassistant.components import bluetooth
    from homeassistant.exceptions import ConfigEntryNotReady

    from .coordinator import create_coordinator

    _cleanup_deprecated_int14_entities(hass, entry)

    if not bluetooth.async_scanner_count(hass, connectable=True):
        raise ConfigEntryNotReady(
            "No connectable Bluetooth adapter or ESPHome proxy is available"
        )

    coordinator = create_coordinator(
        hass,
        entry,
        model=entry.data[CONF_MODEL],
        address=entry.data[CONF_ADDRESS],
    )
    entry.runtime_data = coordinator
    await coordinator.async_start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> bool:
    """Unload an INKBIRD BBQ config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded
