# Changelog

All notable changes to this project will be documented here.

The project is currently in pre-release development.

## 0.1.0-dev.4

- Physically validated INT-14-BW probe-target writes against both the base display and INKBIRD app.
- Confirmed target behavior remains correct through C -> F -> C unit switching.
- Changed INT-14-BW target number entities to follow the device's selected display unit, showing and accepting °C or °F as appropriate.
- Added startup reads with FF02 readback/retry for temperature unit and display brightness so these controls populate from the device instead of starting as unknown.
- Confirmed INT-14-BW reconnect after ESPHome Bluetooth Proxy restart.
- Confirmed INT-14-BW reconnect after Home Assistant restart.
- Reconfirmed simultaneous Home Assistant BLE operation and INKBIRD app monitoring over Wi-Fi.

## 0.1.0-dev.3

- Merged the initial integration development branch to \`main\`.
- Enabled automatic TNT-11-B discovery through its physically confirmed \`BG-BT1W\` Bluetooth name.
- Added the TNT-11-B coordinator and live probe-temperature sensor.
- Corrected TNT-11-B temperature decoding from an experimental /100 scale to the physically confirmed whole-degree signed little-endian value; real packet \`19 00 18 71\` now reports 25 °C.
- Added INT-14-BW target controls for probes 1-4.
- Normalized INT-14-BW target reports from Fahrenheit x10 on the wire to Celsius in Home Assistant and added Celsius-to-wire conversion for writes.
- Added target readback verification after INT-14-BW probe-target writes.
- Removed obsolete INT-14-BW Wi-Fi/auto-sleep/read-only development entities from the entity registry while retaining confirmed C/F and display-brightness controls.
- Kept ISC-027BW pit target, probe alarms and fan on/off controls with physical readback validation.
- Expanded CI with Python compile checks, JSON/YAML validation, Home Assistant import smoke tests, metadata checks, icon validation, Ruff and pytest.
- Added Bandit, pip-audit, Gitleaks and CodeQL security workflows.
- Added official HACS Validation and validated the repository metadata/topics successfully.
- Updated README, HACS installation guidance, protocol research and physical hardware validation documentation.

## 0.1.0-dev.2

- Added Home Assistant Bluetooth discovery for ISC-027BW and INT-14-BW.
- Added the physically confirmed ISC-027BW advertisement name \`S27\` with vendor service FFF0.
- Validated the first physical INT-14-BW session through the Olimex ESPHome Bluetooth proxy, including battery values, all four dock states and probe 1 core/ambient temperature reporting.
- Confirmed probe 1 return-to-dock behavior and probe 2 channel mapping with distinct core/ambient values.
- Confirmed probe 3 and probe 4 dock/undock mapping and temperature reporting on physical hardware.
- Confirmed automatic reconnect after power-cycling the physical INT-14-BW base station through the Olimex Bluetooth proxy.
- Confirmed INT-14-BW BLE coexistence with the INKBIRD iPhone app over Wi-Fi.
- Added local Home Assistant brand icons and CI validation for their dimensions/decoding.
- Added persistent model-specific BLE coordinators with reconnect handling.
- Added Bluetooth reconnect-loop tests.
- Added ISC-027BW protocol decoding with CRC16-Modbus validation.
- Added ISC-027BW temperatures, targets, fan output/state and experimental write controls.
- Confirmed on physical ISC-027BW hardware that fan output is automatically regulated, BLE fan on/off works and the controller disables the fan when the grill/pit probe is absent.
- Added INT-14-BW challenge/response authentication, telemetry, battery and dock-state handling.
- Added English base strings and Dutch translations.
- Added privacy-safe Home Assistant diagnostics.
- Added protocol, config-flow and coordinator tests.
- Added the interactive Git updater with backup, \`ha core check\` and rollback.
- Documented the Olimex ESP32-POE-ISO-EA reference Bluetooth proxy.

## 0.1.0-dev.1

- Initial Home Assistant/HACS repository skeleton.
- Added initial protocol research structure for ISC-027BW, INT-14-BW and TNT-11-B.
