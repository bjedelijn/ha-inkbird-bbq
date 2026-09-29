"""Tests for INKBIRD BBQ binary entity definitions."""

from custom_components.inkbird_bbq.binary_sensor import (
    INT14BW_BINARY_SENSORS,
    ISC027BW_BINARY_SENSORS,
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
