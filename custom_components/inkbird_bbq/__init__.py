"""INKBIRD BBQ integration for Home Assistant."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_MODEL
from .coordinator import InkbirdBbqCoordinator, create_coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type InkbirdBbqConfigEntry = ConfigEntry[InkbirdBbqCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> bool:
    """Set up INKBIRD BBQ from a config entry."""
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
