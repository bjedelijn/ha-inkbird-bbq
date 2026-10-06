"""Shared Bluetooth connection helpers for INKBIRD BBQ devices."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from homeassistant.core import callback

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DEFAULT_ADVERTISEMENT_TIMEOUT = 30.0
DEFAULT_RECONNECT_DELAY = 10.0


class InkbirdBluetoothConnection:
    """Resolve and connect through Home Assistant's Bluetooth stack.

    Home Assistant chooses the best connectable source, which may be a local
    Bluetooth adapter or a remote ESPHome Bluetooth proxy.
    """

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address.upper()
        self.name = name

    async def async_wait_for_advertisement(
        self, timeout: float = DEFAULT_ADVERTISEMENT_TIMEOUT
    ) -> BLEDevice | None:
        """Wait for a fresh advertisement and return HA's selected BLEDevice."""
        from homeassistant.components import bluetooth
        from homeassistant.components.bluetooth import BluetoothCallbackMatcher

        event = asyncio.Event()
        found: dict[str, BLEDevice] = {}

        @callback
        def _on_advertisement(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            _change: bluetooth.BluetoothChange,
        ) -> None:
            found["device"] = service_info.device
            event.set()

        unregister = bluetooth.async_register_callback(
            self.hass,
            _on_advertisement,
            BluetoothCallbackMatcher(address=self.address, connectable=True),
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
        try:
            with contextlib.suppress(TimeoutError, asyncio.TimeoutError):
                await asyncio.wait_for(event.wait(), timeout)
        finally:
            unregister()

        return found.get("device")

    async def async_resolve_device(self) -> BLEDevice | None:
        """Resolve a connectable device, preferring a fresh advertisement."""
        from homeassistant.components import bluetooth

        device = await self.async_wait_for_advertisement()
        if device is not None:
            return device

        return bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )

    async def async_connect(self, device: BLEDevice) -> BleakClient:
        """Connect using bleak-retry-connector."""
        return await establish_connection(
            BleakClient,
            device,
            self.name,
            max_attempts=2,
        )


async def async_connection_loop(
    connection: InkbirdBluetoothConnection,
    session: Callable[[BleakClient], Awaitable[None]],
    stop_event: asyncio.Event,
) -> None:
    """Run a resilient connect/session/reconnect loop."""
    while not stop_event.is_set():
        device = await connection.async_resolve_device()
        if device is None:
            await _sleep_or_stop(stop_event, DEFAULT_RECONNECT_DELAY)
            continue

        client: BleakClient | None = None
        try:
            client = await connection.async_connect(device)
            await session(client)
        except asyncio.CancelledError:
            raise
        except Exception as err:  # noqa: BLE001 - resilience boundary
            _LOGGER.debug(
                "Bluetooth session for %s ended: %s", connection.address, err
            )
        finally:
            if client is not None and client.is_connected:
                with contextlib.suppress(Exception):
                    await client.disconnect()

        await _sleep_or_stop(stop_event, DEFAULT_RECONNECT_DELAY)


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    """Sleep until timeout or stop request."""
    with contextlib.suppress(TimeoutError, asyncio.TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
