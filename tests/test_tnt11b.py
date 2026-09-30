"""Tests for BG-BT1W / TNT-11-B protocol decoding."""

from __future__ import annotations

import struct

import pytest

from custom_components.inkbird_bbq.devices.tnt11b import decode_notification


def test_decode_food_temperature() -> None:
    data = bytes.fromhex("19 00 18 71")
    reading = decode_notification(data)
    assert reading.food_temperature == 25.0
    assert reading.raw == data


def test_decode_negative_temperature() -> None:
    reading = decode_notification(struct.pack("<h", -12))
    assert reading.food_temperature == -12.0


def test_decode_short_notification_rejected() -> None:
    with pytest.raises(ValueError):
        decode_notification(bytes((0x10,)))
