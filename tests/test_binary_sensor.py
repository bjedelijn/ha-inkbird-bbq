"""Tests for INKBIRD BBQ binary entity definitions."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.inkbird_bbq.binary_sensor import (
    INT14BW_BINARY_SENSORS,
    ISC027BW_BINARY_SENSORS,
    TNT11B_BINARY_SENSORS,
)


def test_isc027bw_exposes_fan_state() -> None:
    assert [description.key for description in ISC027BW_BINARY_SENSORS] == ["fan_on"]


def test_int14bw_exposes_four_dock_states() -> None:
    assert [description.key for description in INT14BW_BINARY_SENSORS] == [
        "probe_1_docked",
        "probe_2_docked",
        "probe_3_docked",
        "probe_4_docked",
    ]


def test_tnt11b_exposes_charging_state() -> None:
    assert [description.key for description in TNT11B_BINARY_SENSORS] == ["charging"]
    assert (
        TNT11B_BINARY_SENSORS[0].device_class
        is BinarySensorDeviceClass.BATTERY_CHARGING
    )
