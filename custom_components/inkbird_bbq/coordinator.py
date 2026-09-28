"""Bluetooth coordinators for INKBIRD BBQ devices."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import logging
from typing import Any

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble import InkbirdBluetoothConnection, async_connection_loop
from .const import MODEL_INT_14_BW, MODEL_ISC_027BW
from .devices.int14bw import (
    CHAR_BATTERY,
    CHAR_CONTROL,
    CHAR_STATE,
    CHAR_TEMPERATURE,
    build_challenge_request,
    build_clock_sync,
    build_verify_response,
    decode_temperatures,
    parse_battery,
    parse_ff02_frames,
)
from .devices.isc027bw import (
    CHAR_FAN,
    CHAR_TARGETS,
    CHAR_TELEMETRY,
    decode_targets,
    decode_telemetry,
)

_LOGGER = logging.getLogger(__name__)

_INT14_CURRENT_INFO_REQUEST = bytes.fromhex(
    "02 f1 01 02 f1 03 02 f1 19"
)


class InkbirdBbqCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Base coordinator for a persistent INKBIRD Bluetooth session."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        model: str,
        address: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"INKBIRD BBQ {model}",
        )
        self.entry = entry
        self.model = model
        self.address = address.upper()
        self.connection = InkbirdBluetoothConnection(
            hass,
            self.address,
            f"INKBIRD BBQ {model}",
        )
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self.data = {
            "model": model,
            "address": self.address,
            "available": False,
        }

    async def async_start(self) -> None:
        """Start the persistent Bluetooth connection loop."""
        self._stop.clear()
        self._task = self.entry.async_create_background_task(
            self.hass,
            async_connection_loop(self.connection, self._session, self._stop),
            f"inkbird_bbq_{self.model}_{self.address}",
        )

    async def async_stop(self) -> None:
        """Stop the Bluetooth connection loop."""
        self._stop.set()
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._set_available(False)

    async def _session(self, client: BleakClient) -> None:
        """Run one model-specific BLE session."""
        raise NotImplementedError

    def _publish(self, **values: Any) -> None:
        """Publish changed coordinator data."""
        updated = dict(self.data)
        updated.update(values)
        self.async_set_updated_data(updated)

    def _set_available(self, available: bool) -> None:
        if self.data.get("available") != available:
            self._publish(available=available)


class Isc027bwCoordinator(InkbirdBbqCoordinator):
    """Read-only ISC-027BW coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            entry,
            model=MODEL_ISC_027BW,
            address=address,
        )

    async def _session(self, client: BleakClient) -> None:
        self._set_available(True)

        async def _read_once() -> None:
            telemetry_raw = bytes(await client.read_gatt_char(CHAR_TELEMETRY))
            telemetry = decode_telemetry(telemetry_raw)

            values: dict[str, Any] = {
                "pit_temperature": telemetry.pit_temperature,
                "meat_probe_1": telemetry.meat_probe_1,
                "meat_probe_2": telemetry.meat_probe_2,
                "meat_probe_3": telemetry.meat_probe_3,
                "fan_output": telemetry.fan_output,
            }

            try:
                targets_raw = bytes(await client.read_gatt_char(CHAR_TARGETS))
                targets = decode_targets(targets_raw)
                values.update(
                    pit_target=targets.pit_target,
                    meat_probe_1_alarm=targets.meat_probe_1_alarm,
                    meat_probe_2_alarm=targets.meat_probe_2_alarm,
                    meat_probe_3_alarm=targets.meat_probe_3_alarm,
                )
            except Exception as err:  # noqa: BLE001 - optional read path
                _LOGGER.debug("ISC-027BW FFF3 read failed: %s", err)

            try:
                fan_raw = bytes(await client.read_gatt_char(CHAR_FAN))
                if fan_raw:
                    values["fan_on"] = bool(fan_raw[0])
            except Exception as err:  # noqa: BLE001 - optional read path
                _LOGGER.debug("ISC-027BW FFF1 read failed: %s", err)

            self._publish(**values)

        while client.is_connected and not self._stop.is_set():
            await _read_once()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=5)
            except TimeoutError:
                pass

        self._set_available(False)


class Int14bwCoordinator(InkbirdBbqCoordinator):
    """Authenticated read-only INT-14-BW coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            entry,
            model=MODEL_INT_14_BW,
            address=address,
        )
        self._challenge: bytes | None = None
        self._challenge_event = asyncio.Event()
        self._auth_event = asyncio.Event()
        self._docked = [False] * 4

    async def _session(self, client: BleakClient) -> None:
        self._challenge = None
        self._challenge_event.clear()
        self._auth_event.clear()

        await client.start_notify(CHAR_CONTROL, self._on_control)
        await client.start_notify(CHAR_TEMPERATURE, self._on_temperature)

        with contextlib.suppress(Exception):
            await client.start_notify(CHAR_STATE, self._on_state)

        with contextlib.suppress(Exception):
            await client.start_notify(CHAR_BATTERY, self._on_battery)
            self._on_battery(
                None,
                bytearray(await client.read_gatt_char(CHAR_BATTERY)),
            )

        await client.write_gatt_char(
            CHAR_CONTROL,
            build_challenge_request(),
            response=False,
        )
        await asyncio.wait_for(self._challenge_event.wait(), timeout=8)

        if self._challenge is None:
            raise RuntimeError("INT-14-BW challenge event without challenge")

        await client.write_gatt_char(
            CHAR_CONTROL,
            build_verify_response(self._challenge),
            response=False,
        )

        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._auth_event.wait(), timeout=5)

        await client.write_gatt_char(
            CHAR_CONTROL,
            build_clock_sync(),
            response=False,
        )
        await client.write_gatt_char(
            CHAR_CONTROL,
            _INT14_CURRENT_INFO_REQUEST,
            response=False,
        )

        self._set_available(True)

        while client.is_connected and not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=10)
            except TimeoutError:
                await client.write_gatt_char(
                    CHAR_CONTROL,
                    _INT14_CURRENT_INFO_REQUEST,
                    response=False,
                )

        self._set_available(False)

    def _on_control(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        try:
            frames = parse_ff02_frames(bytes(data))
        except ValueError as err:
            _LOGGER.debug("Ignoring malformed INT-14-BW FF02 frame: %s", err)
            return

        for frame_type, payload in frames:
            if frame_type == 0xFB and len(payload) == 6:
                self._challenge = payload
                self._challenge_event.set()
            elif frame_type == 0xFC and payload and payload[0] == 0x00:
                self._auth_event.set()

    def _on_temperature(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        try:
            decoded = decode_temperatures(bytes(data))
        except ValueError as err:
            _LOGGER.debug("Ignoring malformed INT-14-BW FF01 frame: %s", err)
            return

        values: dict[str, Any] = {}
        for index in range(4):
            suffix = index + 1
            values[f"probe_{suffix}_core"] = (
                None if self._docked[index] else decoded.core[index]
            )
            values[f"probe_{suffix}_ambient"] = (
                None if self._docked[index] else decoded.ambient[index]
            )
        self._publish(**values)

    def _on_state(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        # Public implementations disagree on the exact FF03 state layout
        # across firmware revisions. The first eight bytes consistently
        # represent four status pairs on the tested INT-14-BW firmware.
        for index in range(4):
            offset = index * 2
            if offset < len(data):
                self._docked[index] = bool(data[offset] & 0x02)

        values = {
            f"probe_{index + 1}_docked": docked
            for index, docked in enumerate(self._docked)
        }
        self._publish(**values)

    def _on_battery(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        batteries = parse_battery(bytes(data))
        values: dict[str, Any] = {}
        if batteries:
            values["base_battery"] = batteries[0]
        for index, value in enumerate(batteries[1:5], start=1):
            values[f"probe_{index}_battery"] = value
        self._publish(**values)


def create_coordinator(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    model: str,
    address: str,
) -> InkbirdBbqCoordinator:
    """Create a model-specific coordinator."""
    if model == MODEL_ISC_027BW:
        return Isc027bwCoordinator(hass, entry, address)
    if model == MODEL_INT_14_BW:
        return Int14bwCoordinator(hass, entry, address)
    raise ValueError(f"Unsupported INKBIRD BBQ model: {model}")
