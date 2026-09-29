"""Diagnostics support for INKBIRD BBQ."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import InkbirdBbqConfigEntry

_TO_REDACT = {
    "address",
}


def _build_diagnostics(
    entry_data: dict[str, Any],
    *,
    model: str,
    coordinator_data: dict[str, Any],
) -> dict[str, Any]:
    """Build privacy-safe diagnostics data."""
    return {
        "entry": async_redact_data(dict(entry_data), _TO_REDACT),
        "model": model,
        "available": bool(coordinator_data.get("available")),
        "data": async_redact_data(dict(coordinator_data), _TO_REDACT),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: InkbirdBbqConfigEntry,
) -> dict[str, Any]:
    """Return privacy-safe diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return _build_diagnostics(
        dict(entry.data),
        model=coordinator.model,
        coordinator_data=dict(coordinator.data),
    )
