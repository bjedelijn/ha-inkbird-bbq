"""Tests for INKBIRD BBQ sensor entity definitions."""

from custom_components.inkbird_bbq.sensor import INT14BW_SENSORS


def test_int14bw_exposes_read_only_settings_sensors() -> None:
    keys = {description.key for description in INT14BW_SENSORS}

    assert {
        "temperature_unit",
        "display_brightness",
        "auto_sleep_minutes",
    } <= keys
