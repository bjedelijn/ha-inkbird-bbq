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
    raw: bytes


def decode_notification(data: bytes) -> Tnt11bReading:
    """Decode the confirmed food-temperature field from FF03."""
    if len(data) < 2:
        raise ValueError("BG-BT1W FF03 notification is shorter than 2 bytes")

    raw_value = struct.unpack_from("<h", data, 0)[0]
    return Tnt11bReading(
        food_temperature=round(raw_value / 100.0, 2),
        raw=bytes(data),
    )
