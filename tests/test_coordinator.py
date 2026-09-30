"""Tests for read-only coordinator callback handling."""

from __future__ import annotations

import asyncio
import struct
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.inkbird_bbq.coordinator import Int14bwCoordinator
from custom_components.inkbird_bbq.devices.int14bw import (
    build_verify_response,
)


def _coordinator_stub() -> tuple[Int14bwCoordinator, list[dict[str, Any]]]:
    coordinator = object.__new__(Int14bwCoordinator)
    coordinator._challenge = None
    coordinator._challenge_event = asyncio.Event()
    coordinator._auth_event = asyncio.Event()
    coordinator._docked = [False] * 4
    published: list[dict[str, Any]] = []
    coordinator._publish = lambda **values: published.append(values)
    return coordinator, published


def test_control_callback_captures_challenge_and_ack() -> None:
    coordinator, _published = _coordinator_stub()
    challenge = bytes.fromhex("2a 19 e1 1e 78 aa")

    coordinator._on_control(
        None,
        bytearray(bytes((0x07, 0xFB)) + challenge),
    )
    assert coordinator._challenge == challenge
    assert coordinator._challenge_event.is_set()

    coordinator._on_control(None, bytearray(bytes.fromhex("02 fc 00")))
    assert coordinator._auth_event.is_set()

    # Sanity-check that the captured challenge is usable by the auth builder.
    assert len(build_verify_response(challenge, timestamp_ms=1_779_980_959_482)) == 9


def test_temperature_callback_maps_four_probe_pairs() -> None:
    coordinator, published = _coordinator_stub()
    frame = bytearray(16)
    values = (635, 250, 700, 260, 800, 270, 900, 280)
    for offset, value in zip(range(0, 16, 2), values, strict=True):
        struct.pack_into("<h", frame, offset, value)

    coordinator._on_temperature(None, frame)

    assert published[-1] == {
        "probe_1_core": 63.5,
        "probe_1_ambient": 25.0,
        "probe_2_core": 70.0,
        "probe_2_ambient": 26.0,
        "probe_3_core": 80.0,
        "probe_3_ambient": 27.0,
        "probe_4_core": 90.0,
        "probe_4_ambient": 28.0,
    }


def test_docked_probe_suppresses_temperature_values() -> None:
    coordinator, published = _coordinator_stub()
    coordinator._docked[1] = True

    frame = bytearray(16)
    for offset, value in zip(
        range(0, 16, 2),
        (635, 250, 700, 260, 800, 270, 900, 280),
        strict=True,
    ):
        struct.pack_into("<h", frame, offset, value)

    coordinator._on_temperature(None, frame)

    assert published[-1]["probe_2_core"] is None
    assert published[-1]["probe_2_ambient"] is None
    assert published[-1]["probe_1_core"] == 63.5


def test_state_callback_updates_four_dock_states() -> None:
    coordinator, published = _coordinator_stub()

    coordinator._on_state(
        None,
        bytearray((0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00)),
    )

    assert coordinator._docked == [False, True, False, True]
    assert published[-1] == {
        "probe_1_docked": False,
        "probe_2_docked": True,
        "probe_3_docked": False,
        "probe_4_docked": True,
    }


def test_battery_callback_maps_base_and_probe_values() -> None:
    coordinator, published = _coordinator_stub()

    coordinator._on_battery(None, bytearray((88, 91, 92, 0x7F, 94)))

    assert published[-1] == {
        "base_battery": 88,
        "probe_1_battery": 91,
        "probe_2_battery": 92,
        "probe_3_battery": None,
        "probe_4_battery": 94,
    }


@pytest.mark.asyncio
async def test_int14_setting_write_requests_readback() -> None:
    coordinator, published = _coordinator_stub()
    coordinator._io_lock = asyncio.Lock()
    client = MagicMock()
    client.is_connected = True
    client.write_gatt_char = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=bytes.fromhex("02 06 32"))
    coordinator._client = client

    await coordinator.async_set_display_brightness(50)

    assert (
        client.write_gatt_char.await_args_list[0].args[1]
        == bytes.fromhex("02 05 32")
    )
    assert (
        client.write_gatt_char.await_args_list[1].args[1]
        == bytes.fromhex("01 06")
    )
    assert {"display_brightness": 50} in published
