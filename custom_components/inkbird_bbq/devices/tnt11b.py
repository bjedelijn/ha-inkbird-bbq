"""Protocol support for the INKBIRD BG-BT1W / TNT-11-B."""

from __future__ import annotations

import struct
from dataclasses import dataclass

MODEL = "TNT-11-B"
LOCAL_NAME = "BG-BT1W"

SERVICE_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
CHAR_CONTROL = "0000ff02-0000-1000-8000-00805f9b34fb"
CHAR_TEMPERATURE = "0000ff03-0000-1000-8000-00805f9b34fb"
CHAR_COMMAND = "0000ff04-0000-1000-8000-00805f9b34fb"


@dataclass(frozen=True, slots=True)
class Tnt11bReading:
    """Decoded confirmed fields from one FF03 notification."""

    food_temperature: float
    ambient_temperature: float | None
    battery_raw: int | None
    raw: bytes


def decode_notification(data: bytes) -> Tnt11bReading:
    """Decode the food-temperature field from a BG-BT1W FF03 notification."""
    if len(data) < 2:
        raise ValueError("BG-BT1W FF03 notification is shorter than 2 bytes")

    # Physical BG-BT1W validation and independent packet captures show the
    # first two bytes are a signed little-endian integer in whole degrees C.
    raw_value = struct.unpack_from("<h", data, 0)[0]
    return Tnt11bReading(
        food_temperature=float(raw_value),
        ambient_temperature=float(data[2]) if len(data) >= 3 else None,
        battery_raw=data[3] if len(data) >= 4 else None,
        raw=bytes(data),
    )
