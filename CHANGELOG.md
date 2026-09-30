# Changelog

All notable changes to this project will be documented here.

The project is currently in pre-release development.

## 0.1.0-dev.2

- Added Home Assistant Bluetooth discovery for ISC-027BW and INT-14-BW.
- Validated the first physical INT-14-BW session through the Olimex ESPHome Bluetooth proxy, including battery values, all four dock states and probe 1 core/ambient temperature reporting.
- Confirmed probe 1 return-to-dock behavior and probe 2 channel mapping with distinct 27.0 °C core / 24.0 °C ambient values.
- Added a local Home Assistant brand icon representing probes, wireless BBQ monitoring and planned blower/fan control.
- Added explicit dark and HiDPI brand icon variants so Home Assistant's local Brands API does not fall back to the placeholder for `dark_icon@2x.png`.
- Added persistent model-specific BLE coordinators with reconnect handling.
- Added Bluetooth reconnect-loop tests for missing devices, session failures, disconnect cleanup and cancellation.
- Added read-only ISC-027BW protocol decoding with CRC16-Modbus validation.
- Added read-only ISC-027BW temperature, target, fan-output and fan-state entities.
- Added INT-14-BW challenge/response authentication, clock sync and frame parsing.
- Added read-only INT-14-BW core/ambient temperature, battery and dock-state entities.
- Added privacy-safe Home Assistant diagnostics and diagnostics privacy tests for Bluetooth-address redaction.
- Added English base strings and initial Dutch translations.
- Added protocol unit tests and CI.\n- Added config-flow and coordinator callback tests for model matching, authentication events, probe mapping, dock state and battery handling.\n- Added ISC-027BW coordinator mapping tests for telemetry, targets, fan state and corrupt-frame rejection.
- Added CI validation for JSON metadata and updater shell syntax.
- CI now cross-checks Home Assistant/HACS metadata and the intended Bluetooth discovery model list.
- Added an interactive Git updater with backup, `ha core check` and rollback.
- Documented the Olimex ESP32-POE-ISO-EA reference Bluetooth proxy.
- Documented BLE/Wi-Fi/vendor-app coexistence goals.
- Added a hardware validation plan for ISC-027BW, INT-14-BW and TNT-11-B.\n- Separated currently supported models from planned TNT-11-B support and added coordinator-factory boundary tests.\n- Pass the config entry explicitly to Home Assistant's DataUpdateCoordinator for current HA compatibility.
- Use Home Assistant's `CONF_ADDRESS` constant consistently when setting up config entries.

## 0.1.0-dev.1

- Initial Home Assistant/HACS repository skeleton.
- Added initial protocol research structure for ISC-027BW, INT-14-BW and TNT-11-B.
