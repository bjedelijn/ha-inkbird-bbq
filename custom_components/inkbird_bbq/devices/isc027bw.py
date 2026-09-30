"""Read-only protocol support for the INKBIRD ISC-027BW."""

from __future__ import annotations

import struct
from dataclasses import dataclass

MODEL = "ISC-027BW"

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_FAN = "0000fff1-0000-1000-8000-00805f9b34fb"
CHAR_TELEMETRY = "0000fff2-0000-1000-8000-00805f9b34fb"
CHAR_TARGETS = "0000fff3-0000-1000-8000-00805f9b34fb"

FRAME_LENGTH = 20
CRC_DATA_LENGTH = 18
_F10_MAX_VALID = 6000
_F10_DISABLED = 0xFFFE


class InvalidFrameError(ValueError):
    """Raised when an ISC-027BW frame is malformed or fails CRC validation."""


@dataclass(frozen=True, slots=True)
class Isc027bwTelemetry:
    """Decoded FFF2 telemetry."""

    pit_temperature: float | None
    meat_probe_1: float | None
    meat_probe_2: float | None
    meat_probe_3: float | None
    fan_output: int | None


@dataclass(frozen=True, slots=True)
class Isc027bwTargets:
    """Decoded FFF3 target values."""

    pit_target: float | None
    meat_probe_1_alarm: float | None
    meat_probe_2_alarm: float | None
    meat_probe_3_alarm: float | None


def crc16_modbus(data: bytes) -> int:
    """Return CRC-16/MODBUS for data."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def validate_frame(data: bytes) -> None:
    """Validate length and CRC of a 20-byte ISC-027BW frame."""
    if len(data) != FRAME_LENGTH:
        raise InvalidFrameError(
            f"Expected {FRAME_LENGTH} bytes, received {len(data)}"
        )

    expected = struct.unpack_from("<H", data, CRC_DATA_LENGTH)[0]
    actual = crc16_modbus(data[:CRC_DATA_LENGTH])
    if actual != expected:
        raise InvalidFrameError(
            f"CRC mismatch: expected 0x{expected:04x}, calculated 0x{actual:04x}"
        )


def fahrenheit10_to_celsius(value: int) -> float | None:
    """Convert device Fahrenheit x10 encoding to Celsius."""
    if value in (0, _F10_DISABLED) or value >= _F10_MAX_VALID:
        return None
    return round(((value / 10.0) - 32.0) * 5.0 / 9.0, 1)


def decode_telemetry(data: bytes) -> Isc027bwTelemetry:
    """Decode an FFF2 telemetry frame after CRC validation."""
    validate_frame(data)

    temperatures = [
        fahrenheit10_to_celsius(struct.unpack_from("<H", data, offset)[0])
        for offset in (0, 2, 4, 6)
    ]
    fan_output = data[8]
    if fan_output > 100:
        fan_output = None

    return Isc027bwTelemetry(
        pit_temperature=temperatures[0],
        meat_probe_1=temperatures[1],
        meat_probe_2=temperatures[2],
        meat_probe_3=temperatures[3],
        fan_output=fan_output,
    )


def decode_targets(data: bytes) -> Isc027bwTargets:
    """Decode read-only target/alarm values from an FFF3 frame."""
    validate_frame(data)

    return Isc027bwTargets(
        pit_target=fahrenheit10_to_celsius(struct.unpack_from("<H", data, 0)[0]),
        meat_probe_1_alarm=fahrenheit10_to_celsius(
            struct.unpack_from("<H", data, 4)[0]
        ),
        meat_probe_2_alarm=fahrenheit10_to_celsius(
            struct.unpack_from("<H", data, 6)[0]
        ),
        meat_probe_3_alarm=fahrenheit10_to_celsius(
            struct.unpack_from("<H", data, 8)[0]
        ),
    )


def celsius_to_fahrenheit10(value: float) -> int:
    """Encode a controlled-test target in Fahrenheit x10.

    The public controller implementation uses 20-300 C as its writable range.
    """
    if not 20.0 <= value <= 300.0:
        raise ValueError("Temperature target must be between 20 and 300 C")
    return round((value * 9.0 / 5.0 + 32.0) * 10.0)


def build_fan_control_frame(
    current: bytes,
    *,
    fan_on: bool | None = None,
    speed: int | None = None,
) -> bytes:
    """Build an FFF1 control frame while preserving unknown bytes."""
    validate_frame(current)
    payload = bytearray(current)

    if fan_on is not None:
        payload[0] = 1 if fan_on else 0

    if speed is not None:
        if not 0 <= speed <= 100:
            raise ValueError("Fan speed must be between 0 and 100")
        payload[6] = speed

    struct.pack_into("<H", payload, CRC_DATA_LENGTH, crc16_modbus(payload[:CRC_DATA_LENGTH]))
    return bytes(payload)


def build_target_control_frame(
    current: bytes,
    *,
    pit_target: float | None = None,
    probe_alarms: dict[int, float] | None = None,
) -> bytes:
    """Build an FFF3 target/alarm frame while preserving unknown bytes."""
    validate_frame(current)
    payload = bytearray(current)

    if pit_target is not None:
        struct.pack_into("<H", payload, 0, celsius_to_fahrenheit10(pit_target))

    if probe_alarms:
        offsets = {1: 4, 2: 6, 3: 8}
        for probe, value in probe_alarms.items():
            if probe not in offsets:
                raise ValueError("Probe alarm index must be 1, 2 or 3")
            struct.pack_into(
                "<H",
                payload,
                offsets[probe],
                celsius_to_fahrenheit10(value),
            )

    struct.pack_into("<H", payload, CRC_DATA_LENGTH, crc16_modbus(payload[:CRC_DATA_LENGTH]))
    return bytes(payload)
