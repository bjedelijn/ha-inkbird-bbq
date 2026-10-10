"""Tests for INKBIRD BBQ sensor entity definitions."""

from homeassistant.helpers.entity import EntityCategory

from custom_components.inkbird_bbq.sensor import INT14BW_SENSORS, TNT11B_SENSORS


def test_int14bw_omits_unreliable_read_settings_sensors() -> None:
    keys = {description.key for description in INT14BW_SENSORS}

    assert {
        "temperature_unit",
        "display_brightness",
        "auto_sleep_minutes",
    }.isdisjoint(keys)


def test_tnt11b_exposes_raw_battery_as_diagnostic_sensor() -> None:
    battery = next(
        description for description in TNT11B_SENSORS if description.key == "battery_raw"
    )
    assert battery.entity_category is EntityCategory.DIAGNOSTIC
