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
    coordinator.data = {}

    def _publish(**values: Any) -> None:
        coordinator.data.update(values)
        published.append(values)

    coordinator._publish = _publish
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


@pytest.mark.asyncio
async def test_int14_startup_reads_unit_and_brightness() -> None:
    coordinator, published = _coordinator_stub()
    client = MagicMock()
    client.write_gatt_char = AsyncMock()
    client.read_gatt_char = AsyncMock(
        side_effect=[
            bytes.fromhex("02 04 43"),
            bytes.fromhex("02 06 32"),
        ]
    )

    await coordinator._async_read_startup_settings(client)

    assert [call.args[1] for call in client.write_gatt_char.await_args_list] == [
        bytes.fromhex("01 04"),
        bytes.fromhex("01 06"),
    ]
    assert {"temperature_unit": "C"} in published
    assert {"display_brightness": 50} in published


@pytest.mark.asyncio
async def test_tnt_gatt_diagnostics_reads_only_readable_vendor_characteristics(
) -> None:
    from custom_components.inkbird_bbq.coordinator import Tnt11bCoordinator
    from custom_components.inkbird_bbq.devices.tnt11b import SERVICE_UUID

    coordinator = object.__new__(Tnt11bCoordinator)
    coordinator.data = {}
    published: list[dict[str, Any]] = []

    def _publish(**values: Any) -> None:
        coordinator.data.update(values)
        published.append(values)

    coordinator._publish = _publish

    readable = MagicMock()
    readable.uuid = "0000ff05-0000-1000-8000-00805f9b34fb"
    readable.properties = ["read"]

    write_only = MagicMock()
    write_only.uuid = "0000ff04-0000-1000-8000-00805f9b34fb"
    write_only.properties = ["write"]

    other_service_char = MagicMock()
    other_service_char.uuid = "00002a19-0000-1000-8000-00805f9b34fb"
    other_service_char.properties = ["read"]

    vendor_service = MagicMock()
    vendor_service.uuid = SERVICE_UUID
    vendor_service.characteristics = [readable, write_only]

    other_service = MagicMock()
    other_service.uuid = "0000180f-0000-1000-8000-00805f9b34fb"
    other_service.characteristics = [other_service_char]

    client = MagicMock()
    client.services = [vendor_service, other_service]
    client.read_gatt_char = AsyncMock(return_value=bytes.fromhex("64"))

    await coordinator._async_collect_gatt_diagnostics(client)

    assert [call.args[0] for call in client.read_gatt_char.await_args_list] == [
        readable,
        other_service_char,
    ]
    assert published[-1]["gatt_read_values"] == {
        readable.uuid: "64",
        other_service_char.uuid: "64",
    }
    assert published[-1]["gatt_characteristic_properties"][write_only.uuid] == [
        "write"
    ]


@pytest.mark.asyncio
async def test_isc_gatt_diagnostics_reads_all_readable_characteristics() -> None:
    from custom_components.inkbird_bbq.coordinator import Isc027bwCoordinator
    from custom_components.inkbird_bbq.devices.isc027bw import SERVICE_UUID

    coordinator = object.__new__(Isc027bwCoordinator)
    coordinator.data = {}
    published: list[dict[str, Any]] = []

    def _publish(**values: Any) -> None:
        coordinator.data.update(values)
        published.append(values)

    coordinator._publish = _publish

    readable_vendor = MagicMock()
    readable_vendor.uuid = "0000fff4-0000-1000-8000-00805f9b34fb"
    readable_vendor.properties = ["read", "notify"]

    write_only_vendor = MagicMock()
    write_only_vendor.uuid = "0000fff5-0000-1000-8000-00805f9b34fb"
    write_only_vendor.properties = ["write"]

    readable_other = MagicMock()
    readable_other.uuid = "00002a00-0000-1000-8000-00805f9b34fb"
    readable_other.properties = ["read"]

    vendor_service = MagicMock()
    vendor_service.uuid = SERVICE_UUID
    vendor_service.characteristics = [readable_vendor, write_only_vendor]

    generic_service = MagicMock()
    generic_service.uuid = "00001800-0000-1000-8000-00805f9b34fb"
    generic_service.characteristics = [readable_other]

    client = MagicMock()
    client.services = [vendor_service, generic_service]
    client.read_gatt_char = AsyncMock(
        side_effect=[bytes.fromhex("0102"), b"S27"]
    )

    await coordinator._async_collect_gatt_diagnostics(client)

    assert [call.args[0] for call in client.read_gatt_char.await_args_list] == [
        readable_vendor,
        readable_other,
    ]
    assert published[-1]["gatt_read_values"] == {
        readable_vendor.uuid: "0102",
        readable_other.uuid: "533237",
    }
    assert published[-1]["gatt_characteristic_properties"][
        write_only_vendor.uuid
    ] == ["write"]
    assert published[-1]["gatt_services"][SERVICE_UUID] == [
        readable_vendor.uuid,
        write_only_vendor.uuid,
    ]
