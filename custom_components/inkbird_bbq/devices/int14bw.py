"""Protocol support for the INKBIRD INT-14-BW.

Protocol behavior is based on public MIT-licensed reverse engineering by
Paul Faure (paul43210/inkbird-bw-ble) and Boris Pustilnik
(boris327/ha-inkbird-int14bw). See docs/PROTOCOL_RESEARCH.md.
"""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass

MODEL = "INT-14-BW"
LOCAL_NAME = "INT-14-BW"
LOCAL_NAME_WH = "INT-14-BW_WH"
SUPPORTED_LOCAL_NAMES = {LOCAL_NAME, LOCAL_NAME_WH}

SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
CHAR_TEMPERATURE = "0000ff01-0000-1000-8000-00805f9b34fb"
CHAR_CONTROL = "0000ff02-0000-1000-8000-00805f9b34fb"
CHAR_STATE = "0000ff03-0000-1000-8000-00805f9b34fb"
CHAR_BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"

NUM_PROBES = 4
PROBE_OFFSETS = (0, 4, 8, 12)
AMBIENT_OFFSETS = (2, 6, 10, 14)

_TEMP_ERROR_VALUES = {32766, 32767, -32768}


@dataclass(frozen=True, slots=True)
class Int14bwTemperatures:
    """Decoded core and ambient temperatures for all four probes."""

    core: tuple[float | None, ...]
    ambient: tuple[float | None, ...]


@dataclass(frozen=True, slots=True)
class Int14bwTargetReport:
    """Decoded target-temperature report from FF02 type 0x02."""

    probe: int
    high_raw: int
    low_raw: int
    doneness: int
    food_code: int


def is_supported_name(name: str | None) -> bool:
    """Return whether a BLE local name is the exact supported model."""
    return name in SUPPORTED_LOCAL_NAMES


def _crc8(data: bytes, poly: int, init: int) -> int:
    """Return a non-reflected, MSB-first CRC-8."""
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def crc8_dvb_s2(data: bytes) -> int:
    """Return CRC-8/DVB-S2."""
    return _crc8(data, 0xD5, 0x00)


def crc8_cdma2000(data: bytes) -> int:
    """Return CRC-8/CDMA2000."""
    return _crc8(data, 0x9B, 0xFF)


def build_challenge_request() -> bytes:
    """Build the FF02 request for a fresh authentication challenge."""
    return bytes((0x01, 0xFB))


def build_verify_response(
    challenge: bytes,
    *,
    timestamp_ms: int | None = None,
) -> bytes:
    """Build the FF02 authentication response for a six-byte challenge.

    Passing timestamp_ms makes protocol tests deterministic. In normal use,
    current wall-clock time is used.
    """
    if len(challenge) != 6:
        raise ValueError("INT-14-BW authentication challenge must be 6 bytes")

    if timestamp_ms is None:
        timestamp_ms = time.time_ns() // 1_000_000

    epoch_seconds, milliseconds = divmod(timestamp_ms, 1000)
    body = bytearray(
        (
            milliseconds & 0xFF,
            (milliseconds >> 8) & 0xFF,
            epoch_seconds & 0xFF,
            (epoch_seconds >> 8) & 0xFF,
            (epoch_seconds >> 16) & 0xFF,
            (epoch_seconds >> 24) & 0xFF,
        )
    )

    inner_crc = crc8_dvb_s2(body)
    challenge_crc = crc8_cdma2000(challenge)
    body.append(crc8_dvb_s2(body + bytes((inner_crc, challenge_crc))))

    return bytes((0x08, 0xFC, *body))


def build_settings_read_requests() -> tuple[bytes, ...]:
    """Build safe, individual FF02 setting reads used after authentication.

    Keep each request as a separate GATT write. This avoids depending on a
    negotiated MTU large enough for a combined init blob and makes ESPHome
    Bluetooth proxy behavior more predictable.
    """
    return (
        bytes.fromhex("01 04"),  # temperature unit
        *(bytes((0x02, 0x02, 1 << index)) for index in range(NUM_PROBES)),
        bytes.fromhex("01 06"),  # display brightness
        bytes.fromhex("01 0c"),  # volume/mute (captured, not interpreted yet)
        bytes.fromhex("01 42"),  # Wi-Fi enabled
        bytes.fromhex("01 41"),  # auto-sleep
    )


def build_clock_sync(*, timestamp_ms: int | None = None) -> bytes:
    """Build the FF02 clock-sync frame."""
    if timestamp_ms is None:
        timestamp_ms = time.time_ns() // 1_000_000

    epoch_seconds, milliseconds = divmod(timestamp_ms, 1000)
    return bytes(
        (
            0x07,
            0x19,
            epoch_seconds & 0xFF,
            (epoch_seconds >> 8) & 0xFF,
            (epoch_seconds >> 16) & 0xFF,
            (epoch_seconds >> 24) & 0xFF,
            milliseconds & 0xFF,
            (milliseconds >> 8) & 0xFF,
        )
    )


def parse_temperature(data: bytes, offset: int) -> float | None:
    """Parse a signed little-endian Celsius x10 value."""
    if offset < 0 or offset + 2 > len(data):
        return None

    value = struct.unpack_from("<h", data, offset)[0]
    if value in _TEMP_ERROR_VALUES:
        return None
    return round(value / 10.0, 1)


def decode_temperatures(data: bytes) -> Int14bwTemperatures:
    """Decode the four core/ambient pairs from FF01 telemetry."""
    if len(data) < 16:
        raise ValueError(f"Expected at least 16 FF01 bytes, received {len(data)}")

    return Int14bwTemperatures(
        core=tuple(parse_temperature(data, offset) for offset in PROBE_OFFSETS),
        ambient=tuple(parse_temperature(data, offset) for offset in AMBIENT_OFFSETS),
    )


def parse_ff02_frames(data: bytes) -> tuple[tuple[int, bytes], ...]:
    """Split concatenated FF02 length/type/payload frames."""
    frames: list[tuple[int, bytes]] = []
    offset = 0

    while offset < len(data):
        frame_length = data[offset]
        if frame_length < 1:
            raise ValueError("Invalid zero-length FF02 frame")

        end = offset + 1 + frame_length
        if end > len(data):
            raise ValueError("Truncated FF02 frame")

        frame_type = data[offset + 1]
        payload = data[offset + 2 : end]
        frames.append((frame_type, payload))
        offset = end

    return tuple(frames)


def parse_battery(data: bytes) -> tuple[int | None, ...]:
    """Parse battery percentages, treating 0x7f as absent/invalid."""
    return tuple(None if value == 0x7F else min(value, 100) for value in data)


def parse_temperature_unit(payload: bytes) -> str | None:
    """Parse FF02 type 0x04 temperature-unit payload."""
    if not payload:
        return None
    if payload[0] == 0x43:
        return "C"
    if payload[0] == 0x46:
        return "F"
    return None


def parse_brightness(payload: bytes) -> int | None:
    """Parse FF02 type 0x06 display brightness."""
    if not payload:
        return None
    return min(payload[0], 100)


def parse_target_report(payload: bytes) -> Int14bwTargetReport | None:
    """Parse the known structural fields of an FF02 type 0x02 target report.

    The target scaling is deliberately left raw until confirmed on physical
    hardware. Public reverse engineering leaves the C/F scaling boundary
    unresolved for target-temperature writes.
    """
    if len(payload) < 8:
        return None

    mask = payload[0]
    if mask not in (0x01, 0x02, 0x04, 0x08):
        return None

    probe = mask.bit_length()
    return Int14bwTargetReport(
        probe=probe,
        high_raw=int.from_bytes(payload[2:4], "little"),
        low_raw=int.from_bytes(payload[4:6], "little"),
        doneness=payload[6],
        food_code=payload[7],
    )


def build_temperature_unit_write(unit: str) -> bytes:
    """Build FF02 temperature-unit write for a controlled hardware test."""
    normalized = unit.upper()
    if normalized not in {"C", "F"}:
        raise ValueError("Temperature unit must be C or F")
    return bytes((0x02, 0x03, ord(normalized)))


def build_brightness_write(percent: int) -> bytes:
    """Build FF02 display-brightness write."""
    if not 0 <= percent <= 100:
        raise ValueError("Brightness must be between 0 and 100")
    return bytes((0x02, 0x05, percent))


def celsius_to_target_raw(value: float) -> int:
    """Encode an INT-14-BW target as degrees Celsius x10."""
    if not 0 <= value <= 100:
        raise ValueError("Target temperature must be between 0 and 100 C")
    return round(value * 10)


def build_target_temperature_write(
    probe: int,
    target_celsius: float,
    *,
    low_raw: int = 0,
    doneness: int = 0,
    food_code: int = 0,
) -> bytes:
    """Build an FF02 target-temperature command for one probe."""
    if probe not in range(1, NUM_PROBES + 1):
        raise ValueError("Probe must be between 1 and 4")
    if not 0 <= low_raw <= 0xFFFF:
        raise ValueError("Low target must fit in an unsigned 16-bit value")
    if not 0 <= doneness <= 0xFF:
        raise ValueError("Doneness must fit in one byte")
    if not 0 <= food_code <= 0xFF:
        raise ValueError("Food code must fit in one byte")

    target_raw = celsius_to_target_raw(target_celsius)
    mask = 1 << (probe - 1)
    return bytes(
        (
            0x09,
            0x01,
            mask,
            0x10,
            target_raw & 0xFF,
            (target_raw >> 8) & 0xFF,
            low_raw & 0xFF,
            (low_raw >> 8) & 0xFF,
            doneness,
            food_code,
        )
    )



