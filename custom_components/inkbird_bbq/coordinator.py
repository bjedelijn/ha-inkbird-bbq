"""Bluetooth coordinators for INKBIRD BBQ devices."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble import InkbirdBluetoothConnection, async_connection_loop
from .const import MODEL_INT_14_BW, MODEL_ISC_027BW, MODEL_TNT_11_B
from .devices.int14bw import (
    CHAR_BATTERY,
    CHAR_CONTROL,
    CHAR_STATE,
    CHAR_TEMPERATURE,
    build_brightness_write,
    build_challenge_request,
    build_clock_sync,
    build_target_temperature_write,
    build_temperature_unit_write,
    build_verify_response,
    decode_temperatures,
    parse_battery,
    parse_brightness,
    parse_ff02_frames,
    parse_target_report,
    parse_temperature_unit,
)
from .devices.isc027bw import (
    CHAR_FAN,
    CHAR_TARGETS,
    CHAR_TELEMETRY,
    build_fan_control_frame,
    build_target_control_frame,
    decode_targets,
    decode_telemetry,
)
from .devices.tnt11b import (
    CHAR_TEMPERATURE as TNT_CHAR_TEMPERATURE,
    decode_notification as decode_tnt_notification,
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
            config_entry=entry,
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
        self._client: BleakClient | None = None
        self._io_lock = asyncio.Lock()
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

    def _require_client(self) -> BleakClient:
        """Return the active BLE client for an explicit control operation."""
        client = self._client
        if client is None or not client.is_connected:
            raise RuntimeError(f"{self.model} is not connected")
        return client


class Isc027bwCoordinator(InkbirdBbqCoordinator):
    """Read-only ISC-027BW coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            entry,
            model=MODEL_ISC_027BW,
            address=address,
        )
        self._fff1_current: bytes | None = None
        self._fff3_current: bytes | None = None

    async def _session(self, client: BleakClient) -> None:
        self._client = client
        self._set_available(True)

        async def _read_once() -> None:
            async with self._io_lock:
                telemetry_raw = bytes(await client.read_gatt_char(CHAR_TELEMETRY))
                values = self._decode_telemetry_values(telemetry_raw)

                try:
                    targets_raw = bytes(await client.read_gatt_char(CHAR_TARGETS))
                    values.update(self._decode_target_values(targets_raw))
                    self._fff3_current = targets_raw
                except Exception as err:  # noqa: BLE001 - optional read path
                    _LOGGER.debug("ISC-027BW FFF3 read failed: %s", err)

                try:
                    fan_raw = bytes(await client.read_gatt_char(CHAR_FAN))
                    values.update(self._decode_fan_values(fan_raw))
                    self._fff1_current = fan_raw
                except Exception as err:  # noqa: BLE001 - optional read path
                    _LOGGER.debug("ISC-027BW FFF1 read failed: %s", err)

                self._publish(**values)

        while client.is_connected and not self._stop.is_set():
            await _read_once()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=5)
            except TimeoutError:
                pass

        self._client = None
        self._set_available(False)

    @staticmethod
    def _decode_telemetry_values(data: bytes) -> dict[str, Any]:
        """Decode an ISC-027BW FFF2 telemetry frame into coordinator values."""
        telemetry = decode_telemetry(data)
        return {
            "pit_temperature": telemetry.pit_temperature,
            "meat_probe_1": telemetry.meat_probe_1,
            "meat_probe_2": telemetry.meat_probe_2,
            "meat_probe_3": telemetry.meat_probe_3,
            "fan_output": telemetry.fan_output,
        }

    @staticmethod
    def _decode_target_values(data: bytes) -> dict[str, Any]:
        """Decode an ISC-027BW FFF3 target frame into coordinator values."""
        targets = decode_targets(data)
        return {
            "pit_target": targets.pit_target,
            "meat_probe_1_alarm": targets.meat_probe_1_alarm,
            "meat_probe_2_alarm": targets.meat_probe_2_alarm,
            "meat_probe_3_alarm": targets.meat_probe_3_alarm,
        }

    @staticmethod
    def _decode_fan_values(data: bytes) -> dict[str, Any]:
        """Decode fan state and configured fan setpoint from FFF1."""
        if not data:
            return {}
        return {"fan_on": bool(data[0])}

    async def async_set_fan_on(self, fan_on: bool) -> None:
        """Experimentally set ISC-027BW fan on/off and verify by readback."""
        client = self._require_client()
        async with self._io_lock:
            current = bytes(await client.read_gatt_char(CHAR_FAN))
            self._fff1_current = current
            self._publish(**self._decode_fan_values(current))
            frame = build_fan_control_frame(current, fan_on=fan_on)
            await client.write_gatt_char(CHAR_FAN, frame, response=True)
            await asyncio.sleep(0.25)
            readback = bytes(await client.read_gatt_char(CHAR_FAN))
            self._fff1_current = readback
            self._publish(**self._decode_fan_values(readback))

    async def async_set_pit_target(self, value: float) -> None:
        """Experimentally set ISC-027BW pit target and verify by readback."""
        await self._async_set_target(pit_target=value)

    async def async_set_probe_alarm(self, probe: int, value: float) -> None:
        """Experimentally set an ISC-027BW probe alarm and verify by readback."""
        await self._async_set_target(probe_alarms={probe: value})

    async def _async_set_target(
        self,
        *,
        pit_target: float | None = None,
        probe_alarms: dict[int, float] | None = None,
    ) -> None:
        client = self._require_client()
        async with self._io_lock:
            current = bytes(await client.read_gatt_char(CHAR_TARGETS))
            self._fff3_current = current
            self._publish(**self._decode_target_values(current))
            frame = build_target_control_frame(
                current,
                pit_target=pit_target,
                probe_alarms=probe_alarms,
            )
            await client.write_gatt_char(CHAR_TARGETS, frame, response=True)
            await asyncio.sleep(0.25)
            readback = bytes(await client.read_gatt_char(CHAR_TARGETS))
            self._fff3_current = readback
            self._publish(**self._decode_target_values(readback))


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
        self._target_reports: dict[int, Any] = {}

    async def _session(self, client: BleakClient) -> None:
        self._client = client
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
        await asyncio.sleep(0.5)
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
                async with self._io_lock:
                    await client.write_gatt_char(
                        CHAR_CONTROL,
                        _INT14_CURRENT_INFO_REQUEST,
                        response=False,
                    )

        self._client = None
        self._set_available(False)

    async def _async_write_setting(
        self,
        command: bytes,
        report_request: bytes,
    ) -> None:
        """Write one experimental INT-14-BW setting and force a readback."""
        client = self._require_client()
        async with self._io_lock:
            _LOGGER.debug("INT-14-BW setting write: %s", command.hex())
            await client.write_gatt_char(CHAR_CONTROL, command, response=False)
            await asyncio.sleep(0.25)
            await client.write_gatt_char(
                CHAR_CONTROL,
                report_request,
                response=False,
            )
            await asyncio.sleep(0.25)

            try:
                raw = bytes(await client.read_gatt_char(CHAR_CONTROL))
            except Exception as err:  # noqa: BLE001 - optional readback path
                _LOGGER.debug(
                    "INT-14-BW FF02 setting readback failed after %s: %s",
                    command.hex(),
                    err,
                )
            else:
                if raw:
                    _LOGGER.debug(
                        "INT-14-BW FF02 setting readback after %s: %s",
                        command.hex(),
                        raw.hex(),
                    )
                    self._on_control(None, bytearray(raw))

    async def async_set_probe_target(
        self,
        probe: int,
        target_celsius: float,
    ) -> None:
        """Set one probe target and verify it with an FF02 report."""
        client = self._require_client()
        if probe not in range(1, 5):
            raise ValueError("Probe must be between 1 and 4")

        async with self._io_lock:
            current = self._target_reports.get(probe)
            if current is None:
                await client.write_gatt_char(
                    CHAR_CONTROL,
                    bytes((0x02, 0x02, 1 << (probe - 1))),
                    response=False,
                )
                await asyncio.sleep(0.25)
                raw = bytes(await client.read_gatt_char(CHAR_CONTROL))
                self._on_control(None, bytearray(raw))
                current = self._target_reports.get(probe)

            if current is None:
                raise RuntimeError(
                    f"No target report received for INT-14-BW probe {probe}"
                )

            frame = build_target_temperature_write(
                probe,
                target_celsius,
                low_raw=current.low_raw,
                doneness=current.doneness,
                food_code=current.food_code,
            )
            _LOGGER.debug(
                "INT-14-BW probe %d target write: %s",
                probe,
                frame.hex(),
            )
            await client.write_gatt_char(
                CHAR_CONTROL,
                frame,
                response=False,
            )
            await asyncio.sleep(0.25)
            await client.write_gatt_char(
                CHAR_CONTROL,
                bytes((0x02, 0x02, 1 << (probe - 1))),
                response=False,
            )
            await asyncio.sleep(0.25)
            raw = bytes(await client.read_gatt_char(CHAR_CONTROL))
            self._on_control(None, bytearray(raw))

            updated = self._target_reports.get(probe)
            if updated is None:
                raise RuntimeError(
                    f"No target readback received for INT-14-BW probe {probe}"
                )

            expected = round(target_celsius * 10)
            if updated.high_raw != expected:
                raise RuntimeError(
                    f"INT-14-BW probe {probe} target readback mismatch: "
                    f"expected {expected}, got {updated.high_raw}"
                )

    async def async_set_temperature_unit(self, unit: str) -> None:
        """Experimentally set C/F on the INT-14-BW."""
        await self._async_write_setting(
            build_temperature_unit_write(unit),
            bytes.fromhex("01 04"),
        )

    async def async_set_display_brightness(self, percent: int) -> None:
        """Experimentally set display brightness on the INT-14-BW."""
        await self._async_write_setting(
            build_brightness_write(percent),
            bytes.fromhex("01 06"),
        )

    def _on_control(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        _LOGGER.debug("INT-14-BW FF02 RX: %s", bytes(data).hex())
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
            elif frame_type == 0x04:
                unit = parse_temperature_unit(payload)
                if unit is not None:
                    self._publish(temperature_unit=unit)
            elif frame_type == 0x06:
                brightness = parse_brightness(payload)
                if brightness is not None:
                    self._publish(display_brightness=brightness)
            elif frame_type == 0x02:
                target = parse_target_report(payload)
                if target is not None:
                    self._target_reports[target.probe] = target
                    self._publish(
                        **{
                            f"probe_{target.probe}_target": round(
                                target.high_raw / 10.0, 1
                            ),
                            f"probe_{target.probe}_target_raw": target.high_raw,
                            f"probe_{target.probe}_target_low_raw": target.low_raw,
                            f"probe_{target.probe}_doneness": target.doneness,
                            f"probe_{target.probe}_food_code": target.food_code,
                        }
                    )
                    _LOGGER.debug(
                        "INT-14-BW target report probe=%d high_raw=%d "
                        "low_raw=%d doneness=%d food=%d",
                        target.probe,
                        target.high_raw,
                        target.low_raw,
                        target.doneness,
                        target.food_code,
                    )
            elif frame_type == 0x0C:
                self._publish(volume_raw=payload.hex())
            else:
                _LOGGER.debug(
                    "INT-14-BW unhandled FF02 frame type=0x%02x payload=%s",
                    frame_type,
                    payload.hex(),
                )

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


class Tnt11bCoordinator(InkbirdBbqCoordinator):
    """Bluetooth coordinator for the BG-BT1W / TNT-11-B."""

    async def _session(self, client: BleakClient) -> None:
        self._client = client
        await client.start_notify(TNT_CHAR_TEMPERATURE, self._on_temperature)
        self._set_available(True)

        while client.is_connected and not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=30)
            except TimeoutError:
                pass

        self._client = None
        self._set_available(False)

    def _on_temperature(
        self,
        _characteristic: BleakGATTCharacteristic | None,
        data: bytearray,
    ) -> None:
        try:
            reading = decode_tnt_notification(bytes(data))
        except ValueError as err:
            _LOGGER.debug("Ignoring malformed BG-BT1W FF03 frame: %s", err)
            return

        self._publish(
            probe_temperature=reading.food_temperature,
            raw_packet=reading.raw.hex(),
        )
        _LOGGER.debug(
            "BG-BT1W FF03 RX: %s -> %.2f C",
            reading.raw.hex(),
            reading.food_temperature,
        )


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
    if model == MODEL_TNT_11_B:
        return Tnt11bCoordinator(hass, entry, address)
    raise ValueError(f"Unsupported INKBIRD BBQ model: {model}")
