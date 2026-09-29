"""Diagnostics support for INKBIRD BBQ."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import InkbirdBbqConfigEntry

_TO_REDACT = {
    "address",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> dict[str, Any]:
    """Return privacy-safe diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "entry": async_redact_data(dict(entry.data), _TO_REDACT),
        "model": coordinator.model,
        "available": bool(coordinator.data.get("available")),
        "data": async_redact_data(dict(coordinator.data), _TO_REDACT),
    }
