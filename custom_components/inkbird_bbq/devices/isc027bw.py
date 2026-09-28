"""Read-only protocol support for the INKBIRD ISC-027BW."""

from __future__ import annotations

from dataclasses import dataclass
import struct

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
