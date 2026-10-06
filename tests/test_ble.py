"""Tests for the resilient Bluetooth connection loop."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.inkbird_bbq import ble


@pytest.mark.asyncio
async def test_connection_loop_retries_when_device_is_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()
    connection.async_resolve_device = AsyncMock(side_effect=[None, None])
    session = AsyncMock()
    stop_event = asyncio.Event()
    sleep_calls = 0

    async def _stop_after_second_sleep(
        event: asyncio.Event, _seconds: float
    ) -> None:
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls == 2:
            event.set()

    monkeypatch.setattr(ble, "_sleep_or_stop", _stop_after_second_sleep)

    await ble.async_connection_loop(connection, session, stop_event)

    assert connection.async_resolve_device.await_count == 2
    session.assert_not_awaited()


@pytest.mark.asyncio
async def test_connection_loop_disconnects_after_session_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    device = object()
    client = MagicMock()
    client.is_connected = True
    client.disconnect = AsyncMock()

    connection = MagicMock()
    connection.address = "AA:BB:CC:DD:EE:FF"
    connection.async_resolve_device = AsyncMock(return_value=device)
    connection.async_connect = AsyncMock(return_value=client)

    session = AsyncMock(side_effect=RuntimeError("test session failure"))
    stop_event = asyncio.Event()

    async def _stop_after_retry(event: asyncio.Event, _seconds: float) -> None:
        event.set()

    monkeypatch.setattr(ble, "_sleep_or_stop", _stop_after_retry)

    await ble.async_connection_loop(connection, session, stop_event)

    connection.async_connect.assert_awaited_once_with(device)
    session.assert_awaited_once_with(client)
    client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_connection_loop_does_not_disconnect_already_disconnected_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    device = object()
    client = MagicMock()
    client.is_connected = False
    client.disconnect = AsyncMock()

    connection = MagicMock()
    connection.address = "AA:BB:CC:DD:EE:FF"
    connection.async_resolve_device = AsyncMock(return_value=device)
    connection.async_connect = AsyncMock(return_value=client)

    session = AsyncMock()
    stop_event = asyncio.Event()

    async def _stop_after_session(_client: object) -> None:
        stop_event.set()

    session.side_effect = _stop_after_session

    async def _no_wait(_event: asyncio.Event, _seconds: float) -> None:
        return None

    monkeypatch.setattr(ble, "_sleep_or_stop", _no_wait)

    await ble.async_connection_loop(connection, session, stop_event)

    client.disconnect.assert_not_awaited()


@pytest.mark.asyncio
async def test_connection_loop_propagates_cancellation() -> None:
    device = object()
    client = MagicMock()
    client.is_connected = True
    client.disconnect = AsyncMock()

    connection = MagicMock()
    connection.async_resolve_device = AsyncMock(return_value=device)
    connection.async_connect = AsyncMock(return_value=client)
    session = AsyncMock(side_effect=asyncio.CancelledError())
    stop_event = asyncio.Event()

    with pytest.raises(asyncio.CancelledError):
        await ble.async_connection_loop(connection, session, stop_event)

    client.disconnect.assert_awaited_once()
