"""Tests for disabled-by-default experimental control entities."""

from custom_components.inkbird_bbq.number import (
    INT14BW_NUMBERS,
    ISC027BW_NUMBERS,
    InkbirdBbqNumber,
)
from custom_components.inkbird_bbq.select import InkbirdTemperatureUnitSelect
from custom_components.inkbird_bbq.switch import InkbirdExperimentalSwitch


def test_control_number_sets_are_model_specific() -> None:
    assert {item.key for item in INT14BW_NUMBERS} == {
        "display_brightness_control",
        "auto_sleep_control",
    }
    assert {item.key for item in ISC027BW_NUMBERS} == {
        "fan_setpoint_control",
        "pit_target_control",
        "probe_1_alarm_control",
        "probe_2_alarm_control",
        "probe_3_alarm_control",
    }


def test_experimental_controls_are_disabled_by_default() -> None:
    assert (
        object.__new__(InkbirdBbqNumber).entity_registry_enabled_default is False
    )
    assert (
        object.__new__(InkbirdTemperatureUnitSelect).entity_registry_enabled_default
        is False
    )
    assert (
        object.__new__(InkbirdExperimentalSwitch).entity_registry_enabled_default
        is False
    )
