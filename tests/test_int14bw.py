"""Tests for the INT-14-BW protocol primitives."""

from __future__ import annotations

import struct

import pytest

from custom_components.inkbird_bbq.devices.int14bw import (
    build_challenge_request,
    build_clock_sync,
    build_settings_read_request,
    build_verify_response,
    crc8_cdma2000,
    crc8_dvb_s2,
    decode_temperatures,
    is_supported_name,
    parse_auto_sleep_minutes,
    parse_battery,
    parse_brightness,
    parse_ff02_frames,
    parse_target_report,
    parse_temperature_unit,
    parse_wifi_enabled,
)


def test_model_name_match_is_exact() -> None:
    """Look-alike models must not be accepted accidentally."""
    assert is_supported_name("INT-14-BW")
    assert is_supported_name("INT-14-BW_WH")
    assert not is_supported_name("INT-14S-BW")
    assert not is_supported_name("INT-12I-BW")
    assert not is_supported_name(None)


def test_challenge_request() -> None:
    assert build_challenge_request() == bytes.fromhex("01 fb")


def test_verify_response_reference_vector() -> None:
    """Published protocol vector must reproduce exactly."""
    challenge = bytes.fromhex("2a 19 e1 1e 78 aa")
    timestamp_ms = 1_779_980_959_482

    assert build_verify_response(
        challenge, timestamp_ms=timestamp_ms
    ) == bytes.fromhex("08 fc e2 01 9f 5a 18 6a 78")


def test_clock_sync_reference_timestamp() -> None:
    timestamp_ms = 1_779_980_959_482
    assert build_clock_sync(timestamp_ms=timestamp_ms) == bytes.fromhex(
        "07 19 9f 5a 18 6a e2 01"
    )


def test_crc_functions_are_stable() -> None:
    """Guard the two CRC algorithms used by authentication."""
    assert crc8_dvb_s2(bytes.fromhex("e2 01 9f 5a 18 6a")) == 0xA7
    assert crc8_cdma2000(bytes.fromhex("2a 19 e1 1e 78 aa")) == 0xF9


def test_decode_four_probe_temperature_pairs() -> None:
    frame = bytearray(16)
    values = (
        635,
        250,
        700,
        260,
        800,
        270,
        900,
        280,
    )
    for offset, value in zip(range(0, 16, 2), values, strict=True):
        struct.pack_into("<h", frame, offset, value)

    decoded = decode_temperatures(bytes(frame))
    assert decoded.core == (63.5, 70.0, 80.0, 90.0)
    assert decoded.ambient == (25.0, 26.0, 27.0, 28.0)


def test_temperature_sentinels_are_none() -> None:
    frame = bytearray(16)
    struct.pack_into("<h", frame, 0, 32767)
    struct.pack_into("<h", frame, 2, -32768)

    decoded = decode_temperatures(bytes(frame))
    assert decoded.core[0] is None
    assert decoded.ambient[0] is None


def test_ff02_concatenated_frames() -> None:
    data = bytes.fromhex("07 fb 2a 19 e1 1e 78 aa 02 fc 00")
    assert parse_ff02_frames(data) == (
        (0xFB, bytes.fromhex("2a 19 e1 1e 78 aa")),
        (0xFC, bytes.fromhex("00")),
    )


def test_truncated_ff02_frame_is_rejected() -> None:
    with pytest.raises(ValueError, match="Truncated"):
        parse_ff02_frames(bytes.fromhex("07 fb 01 02"))


def test_battery_parser() -> None:
    assert parse_battery(bytes((95, 0x7F, 101, 42))) == (95, None, 100, 42)


def test_settings_read_request_contains_safe_read_frames() -> None:
    request = build_settings_read_request()
    assert request.startswith(bytes.fromhex("01 04"))
    assert bytes.fromhex("02 02 01") in request
    assert bytes.fromhex("02 02 02") in request
    assert bytes.fromhex("02 02 04") in request
    assert bytes.fromhex("02 02 08") in request
    assert request.endswith(bytes.fromhex("01 41"))


def test_settings_parsers() -> None:
    assert parse_temperature_unit(bytes.fromhex("43")) == "C"
    assert parse_temperature_unit(bytes.fromhex("46")) == "F"
    assert parse_temperature_unit(bytes.fromhex("00")) is None
    assert parse_brightness(bytes((75,))) == 75
    assert parse_brightness(bytes((150,))) == 100
    assert parse_wifi_enabled(bytes((1,))) is True
    assert parse_wifi_enabled(bytes((0,))) is False
    assert parse_auto_sleep_minutes(bytes.fromhex("01 2c 01")) == 5
    assert parse_auto_sleep_minutes(bytes.fromhex("00 2c 01")) == 0


def test_target_report_keeps_temperature_raw_until_live_validation() -> None:
    report = parse_target_report(bytes.fromhex("02 10 e4 02 00 00 05 00"))
    assert report is not None
    assert report.probe == 2
    assert report.high_raw == 740
    assert report.low_raw == 0
    assert report.doneness == 5
    assert report.food_code == 0

    assert parse_target_report(bytes.fromhex("03 10 e4 02 00 00 05 00")) is None
    assert parse_target_report(bytes.fromhex("02 10 e4")) is None
