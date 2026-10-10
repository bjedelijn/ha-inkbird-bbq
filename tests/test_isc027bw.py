"""Tests for the ISC-027BW protocol decoder."""

from __future__ import annotations

import struct

import pytest

from custom_components.inkbird_bbq.devices.isc027bw import (
    InvalidFrameError,
    build_fan_control_frame,
    build_settings_control_frame,
    build_target_control_frame,
    celsius_to_fahrenheit10,
    crc16_modbus,
    decode_settings,
    decode_targets,
    decode_telemetry,
    fahrenheit10_to_celsius,
)


def _frame(payload: bytes) -> bytes:
    data = bytearray(20)
    data[: len(payload)] = payload
    struct.pack_into("<H", data, 18, crc16_modbus(bytes(data[:18])))
    return bytes(data)


def test_crc16_modbus_known_vector() -> None:
    """CRC-16/MODBUS should match the canonical test vector."""
    assert crc16_modbus(b"123456789") == 0x4B37


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (320, 0.0),
        (2120, 100.0),
        (752, 24.0),
        (0, None),
        (0xFFFE, None),
    ],
)
def test_fahrenheit10_to_celsius(raw: int, expected: float | None) -> None:
    """Device temperature values should convert safely."""
    assert fahrenheit10_to_celsius(raw) == expected


def test_decode_telemetry() -> None:
    """FFF2 should expose pit, three probes and actual fan output."""
    payload = bytearray(18)
    for offset, value in zip((0, 2, 4, 6), (752, 1400, 1500, 1600), strict=True):
        struct.pack_into("<H", payload, offset, value)
    payload[8] = 42

    decoded = decode_telemetry(_frame(bytes(payload)))

    assert decoded.pit_temperature == 24.0
    assert decoded.meat_probe_1 == 60.0
    assert decoded.meat_probe_2 == 65.6
    assert decoded.meat_probe_3 == 71.1
    assert decoded.fan_output == 42


def test_decode_targets() -> None:
    """FFF3 target and meat-probe alarms should decode read-only."""
    payload = bytearray(18)
    struct.pack_into("<H", payload, 0, 2570)  # 257 F = 125 C
    struct.pack_into("<H", payload, 2, 3038)  # 303.8 F = 151 C
    struct.pack_into("<H", payload, 4, 1454)  # 145.4 F = 63 C
    struct.pack_into("<H", payload, 6, 1580)  # 158 F = 70 C
    struct.pack_into("<H", payload, 8, 0xFFFE)
    struct.pack_into("<H", payload, 10, 698)  # 69.8 F = 21 C

    decoded = decode_targets(_frame(bytes(payload)))

    assert decoded.pit_target == 125.0
    assert decoded.pit_high_alarm == 151.0
    assert decoded.pit_low_alarm == 21.0
    assert decoded.meat_probe_1_alarm == 63.0
    assert decoded.meat_probe_2_alarm == 70.0
    assert decoded.meat_probe_3_alarm is None


def test_bad_crc_is_rejected() -> None:
    """Corrupt telemetry must never be exposed as a valid temperature."""
    data = bytearray(_frame(bytes(18)))
    data[3] ^= 0x01

    with pytest.raises(InvalidFrameError):
        decode_telemetry(bytes(data))


def test_bad_length_is_rejected() -> None:
    """Unexpected frame lengths must be rejected."""
    with pytest.raises(InvalidFrameError):
        decode_telemetry(bytes(19))




def test_decode_settings_maps_confirmed_fff1_fields() -> None:
    payload = bytearray(18)
    payload[0] = 1
    payload[1] = 1
    struct.pack_into("<b", payload, 2, 10)
    struct.pack_into("<b", payload, 3, -10)
    struct.pack_into("<b", payload, 4, 5)
    struct.pack_into("<b", payload, 5, -5)
    payload[6] = 1
    payload[7] = 0

    decoded = decode_settings(_frame(bytes(payload)))

    assert decoded.fan_on is True
    assert decoded.temperature_unit == "F"
    assert decoded.pit_calibration == 1.0
    assert decoded.probe_1_calibration == -1.0
    assert decoded.probe_2_calibration == 0.5
    assert decoded.probe_3_calibration == -0.5
    assert decoded.lid_reminder is True
    assert decoded.device_sound is False


def test_build_settings_control_frame_preserves_unknown_fields() -> None:
    payload = bytearray(18)
    payload[8] = 0x71
    current = _frame(bytes(payload))

    updated = build_settings_control_frame(
        current,
        temperature_unit="F",
        calibrations={"pit": 1.0, "probe_3": -1.0},
        lid_reminder=True,
        device_sound=True,
    )

    assert updated[1] == 1
    assert struct.unpack_from("<b", updated, 2)[0] == 10
    assert struct.unpack_from("<b", updated, 5)[0] == -10
    assert updated[6] == 1
    assert updated[7] == 1
    assert updated[8] == 0x71
    assert struct.unpack_from("<H", updated, 18)[0] == crc16_modbus(updated[:18])

def test_build_fan_control_frame_preserves_automatic_control_fields() -> None:
    current = bytearray(_frame(bytes(18)))
    current[6] = 73
    struct.pack_into("<H", current, 18, crc16_modbus(bytes(current[:18])))
    updated = build_fan_control_frame(bytes(current), fan_on=True)

    assert updated[0] == 1
    assert updated[6] == 73
    assert struct.unpack_from("<H", updated, 18)[0] == crc16_modbus(updated[:18])


def test_build_target_control_frame_sets_pit_and_probe_alarm() -> None:
    current = _frame(bytes(18))
    updated = build_target_control_frame(
        current,
        pit_target=110.0,
        pit_high_alarm=151.0,
        pit_low_alarm=21.0,
        probe_alarms={1: 75.0},
    )

    assert struct.unpack_from("<H", updated, 0)[0] == 2300
    assert struct.unpack_from("<H", updated, 2)[0] == 3038
    assert struct.unpack_from("<H", updated, 4)[0] == 1670
    assert struct.unpack_from("<H", updated, 10)[0] == 698
    assert struct.unpack_from("<H", updated, 18)[0] == crc16_modbus(updated[:18])


def test_control_temperature_encoder_bounds() -> None:
    assert celsius_to_fahrenheit10(20.0) == 680
    assert celsius_to_fahrenheit10(300.0) == 5720
    with pytest.raises(ValueError):
        celsius_to_fahrenheit10(19.9)
    with pytest.raises(ValueError):
        celsius_to_fahrenheit10(300.1)
