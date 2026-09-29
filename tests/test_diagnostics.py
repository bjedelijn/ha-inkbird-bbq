"""Tests for privacy-safe INKBIRD BBQ diagnostics."""

from homeassistant.components.diagnostics import REDACTED

from custom_components.inkbird_bbq.diagnostics import _build_diagnostics


def test_diagnostics_redact_bluetooth_address() -> None:
    diagnostics = _build_diagnostics(
        {
            "address": "AA:BB:CC:DD:EE:FF",
            "model": "ISC-027BW",
        },
        model="ISC-027BW",
        coordinator_data={
            "address": "AA:BB:CC:DD:EE:FF",
            "model": "ISC-027BW",
            "available": True,
            "pit_temperature": 110.5,
            "fan_output": 37,
        },
    )

    assert diagnostics["entry"]["address"] == REDACTED
    assert diagnostics["data"]["address"] == REDACTED
    assert "AA:BB:CC:DD:EE:FF" not in repr(diagnostics)
    assert diagnostics["model"] == "ISC-027BW"
    assert diagnostics["available"] is True
    assert diagnostics["data"]["pit_temperature"] == 110.5
    assert diagnostics["data"]["fan_output"] == 37


def test_diagnostics_preserve_unavailable_state() -> None:
    diagnostics = _build_diagnostics(
        {"address": "11:22:33:44:55:66"},
        model="INT-14-BW",
        coordinator_data={
            "address": "11:22:33:44:55:66",
            "available": False,
        },
    )

    assert diagnostics["available"] is False
    assert diagnostics["entry"]["address"] == REDACTED
    assert diagnostics["data"]["address"] == REDACTED
