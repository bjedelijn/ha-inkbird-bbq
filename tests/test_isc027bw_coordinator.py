"""Tests for ISC-027BW coordinator value mapping."""

from __future__ import annotations

import struct

import pytest

from custom_components.inkbird_bbq.coordinator import Isc027bwCoordinator
from custom_components.inkbird_bbq.devices.isc027bw import (
    InvalidFrameError,
    crc16_modbus,
)


def _frame(payload: bytes) -> bytes:
    data = bytearray(20)
    data[: len(payload)] = payload
    struct.pack_into("<H", data, 18, crc16_modbus(bytes(data[:18])))
    return bytes(data)


def test_telemetry_values_map_to_entities() -> None:
    payload = bytearray(18)
    for offset, value in zip((0, 2, 4, 6), (752, 1400, 1500, 1600), strict=True):
        struct.pack_into("<H", payload, offset, value)
    payload[8] = 42

    assert Isc027bwCoordinator._decode_telemetry_values(_frame(payload)) == {
        "pit_temperature": 24.0,
        "meat_probe_1": 60.0,
        "meat_probe_2": 65.6,
        "meat_probe_3": 71.1,
        "fan_output": 42,
    }


def test_target_values_map_to_entities() -> None:
    payload = bytearray(18)
    struct.pack_into("<H", payload, 0, 2570)
    struct.pack_into("<H", payload, 2, 3038)
    struct.pack_into("<H", payload, 4, 1454)
    struct.pack_into("<H", payload, 6, 1580)
    struct.pack_into("<H", payload, 8, 0xFFFE)
    struct.pack_into("<H", payload, 10, 698)

    assert Isc027bwCoordinator._decode_target_values(_frame(payload)) == {
        "pit_target": 125.0,
        "pit_high_alarm": 151.0,
        "pit_low_alarm": 21.0,
        "meat_probe_1_alarm": 63.0,
        "meat_probe_2_alarm": 70.0,
        "meat_probe_3_alarm": None,
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"", {}),
        (bytes((0,)), {"fan_on": False}),
        (bytes((1,)), {"fan_on": True}),
        (bytes((100,)), {"fan_on": True}),
    ],
)
def test_fan_state_mapping(raw: bytes, expected: dict[str, bool]) -> None:
    assert Isc027bwCoordinator._decode_fan_values(raw) == expected


def test_corrupt_telemetry_is_not_mapped() -> None:
    data = bytearray(_frame(bytes(18)))
    data[0] ^= 0x01

    with pytest.raises(InvalidFrameError):
        Isc027bwCoordinator._decode_telemetry_values(bytes(data))


def test_corrupt_target_frame_is_not_mapped() -> None:
    data = bytearray(_frame(bytes(18)))
    data[4] ^= 0x01

    with pytest.raises(InvalidFrameError):
        Isc027bwCoordinator._decode_target_values(bytes(data))
