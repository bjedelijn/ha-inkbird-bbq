"""Tests for confirmed INKBIRD BBQ control entities."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.const import UnitOfTemperature

from custom_components.inkbird_bbq.const import MODEL_INT_14_BW
from custom_components.inkbird_bbq.coordinator import Int14bwCoordinator
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
        "probe_1_target_control",
        "probe_2_target_control",
        "probe_3_target_control",
        "probe_4_target_control",
    }
    assert {item.key for item in ISC027BW_NUMBERS} == {
        "pit_target_control",
        "probe_1_alarm_control",
        "probe_2_alarm_control",
        "probe_3_alarm_control",
    }


def test_confirmed_controls_are_enabled_by_default() -> None:
    assert object.__new__(InkbirdBbqNumber).entity_registry_enabled_default is True
    assert (
        object.__new__(InkbirdTemperatureUnitSelect).entity_registry_enabled_default
        is True
    )
    assert (
        object.__new__(InkbirdExperimentalSwitch).entity_registry_enabled_default
        is True
    )


def _int14_target_entity(unit: str, target_celsius: float) -> InkbirdBbqNumber:
    coordinator = object.__new__(Int14bwCoordinator)
    coordinator.address = "AA:BB:CC:DD:EE:FF"
    coordinator.model = MODEL_INT_14_BW
    coordinator.data = {
        "available": True,
        "temperature_unit": unit,
        "probe_1_target": target_celsius,
    }
    description = next(
        item for item in INT14BW_NUMBERS if item.key == "probe_1_target_control"
    )
    return InkbirdBbqNumber(coordinator, description)


def test_int14_target_display_follows_device_temperature_unit() -> None:
    celsius = _int14_target_entity("C", 70.0)
    assert celsius.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert celsius.native_value == 70.0
    assert celsius.native_min_value == 0.0
    assert celsius.native_max_value == 100.0

    fahrenheit = _int14_target_entity("F", 70.0)
    assert fahrenheit.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert fahrenheit.native_value == 158.0
    assert fahrenheit.native_min_value == 32.0
    assert fahrenheit.native_max_value == 212.0


@pytest.mark.asyncio
async def test_int14_target_fahrenheit_input_is_converted_to_celsius() -> None:
    entity = _int14_target_entity("F", 70.0)
    coordinator = entity.coordinator
    coordinator.async_set_probe_target = AsyncMock()

    await entity.async_set_native_value(158.0)

    coordinator.async_set_probe_target.assert_awaited_once_with(1, 70.0)
