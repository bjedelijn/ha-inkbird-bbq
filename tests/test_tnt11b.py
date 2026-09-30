"""Tests for BG-BT1W / TNT-11-B protocol decoding."""

from __future__ import annotations

import struct

import pytest

from custom_components.inkbird_bbq.devices.tnt11b import decode_notification


def test_decode_food_temperature() -> None:
    data = struct.pack("<h", 2345) + bytes.fromhex("7a 62")
    reading = decode_notification(data)
    assert reading.food_temperature == 23.45
    assert reading.raw == data


def test_decode_negative_temperature() -> None:
    reading = decode_notification(struct.pack("<h", -1250))
    assert reading.food_temperature == -12.5


def test_decode_short_notification_rejected() -> None:
    with pytest.raises(ValueError):
        decode_notification(bytes((0x10,)))
