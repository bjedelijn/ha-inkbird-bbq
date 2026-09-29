# Changelog

All notable changes to this project will be documented here.

The project is currently in pre-release development.

## 0.1.0-dev.2

- Added Home Assistant Bluetooth discovery for ISC-027BW and INT-14-BW.
- Added persistent model-specific BLE coordinators with reconnect handling.
- Added read-only ISC-027BW protocol decoding with CRC16-Modbus validation.
- Added read-only ISC-027BW temperature, target, fan-output and fan-state entities.
- Added INT-14-BW challenge/response authentication, clock sync and frame parsing.
- Added read-only INT-14-BW core/ambient temperature, battery and dock-state entities.
- Added privacy-safe Home Assistant diagnostics.
- Added English base strings and initial Dutch translations.
- Added protocol unit tests and CI.
- Added CI validation for JSON metadata and updater shell syntax.
- Added an interactive Git updater with backup, `ha core check` and rollback.
- Documented the Olimex ESP32-POE-ISO-EA reference Bluetooth proxy.
- Documented BLE/Wi-Fi/vendor-app coexistence goals.
- Added a hardware validation plan for ISC-027BW, INT-14-BW and TNT-11-B.

## 0.1.0-dev.1

- Initial Home Assistant/HACS repository skeleton.
- Added initial protocol research structure for ISC-027BW, INT-14-BW and TNT-11-B.
