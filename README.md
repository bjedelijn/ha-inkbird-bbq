# INKBIRD BBQ for Home Assistant

Local Home Assistant integration for INKBIRD BBQ controllers and wireless meat thermometers.

> **Development status:** pre-release. The integration is already usable for hardware testing, but safety-relevant write controls are still considered experimental.

## Supported hardware

Current model support:

- **INKBIRD ISC-027BW** smoker/kamado fan controller
- **INKBIRD INT-14-BW** wireless four-probe meat thermometer
- **INKBIRD TNT-11-B / BG-BT1W** wireless meat thermometer

The integration uses Home Assistant's native Bluetooth stack and works with local Bluetooth adapters as well as ESPHome Bluetooth proxies. Normal operation is local and does not require the INKBIRD cloud.

## Installation with HACS

The repository contains a valid \`hacs.json\` and passes the official HACS Validation workflow.

Until a stable tagged release is published, install it as a **custom HACS repository**:

1. Open HACS in Home Assistant.
2. Add \`https://github.com/bjedelijn/ha-inkbird-bbq\` as a custom repository with category **Integration**.
3. Download **INKBIRD BBQ**.
4. Restart Home Assistant when HACS requests it.
5. Add the discovered INKBIRD device from **Settings -> Devices & services**.

The repository is still pre-release software. HACS currently follows the development version on \`main\`; a stable release/tag will be added later.

## Bluetooth proxy recommendation

For a fixed BBQ/kamado setup, the reference test setup is:

- **Olimex ESP32-POE-ISO-EA**
- **BOX-ESP32-POE-ISO-EA-F** enclosure
- Ethernet/PoE
- external 2.4 GHz antenna
- ESPHome Bluetooth Proxy with active Bluetooth connections enabled

Ethernet avoids sharing an ESP32 radio between Wi-Fi and Bluetooth, PoE gives a simple fixed installation, and Home Assistant can automatically route BLE connections through the proxy.

## Current hardware status

### ISC-027BW

Physically validated through the Olimex Bluetooth proxy:

- discovery as \`S27\` with service FFF0;
- pit temperature and three wired meat-probe temperatures;
- fan running state and actual fan output;
- pit target and three probe alarm targets;
- fan on/off write;
- pit-target write;
- probe-alarm writes;
- immediate GATT readback after writes;
- automatic controller behavior that disables the fan when the grill/pit probe is absent.

Fan output is controlled automatically by the ISC-027BW and is therefore exposed as a measured value, not as a user-settable fan-power percentage.

### INT-14-BW

Physically validated through the Olimex Bluetooth proxy:

- discovery as \`INT-14-BW_WH\`;
- challenge/response authentication and persistent BLE session;
- four probe dock states;
- four core temperatures;
- four ambient temperatures;
- base and probe battery information;
- automatic reconnect after power cycling the base;
- simultaneous Home Assistant BLE use and INKBIRD iPhone app monitoring over Wi-Fi;
- temperature-unit control;
- display-brightness control.

Probe target reports are decoded for all four probes. Hardware observations show that the target value on the wire is Fahrenheit x10 even while Home Assistant exposes the target as Celsius. The integration normalizes these values to Celsius and encodes Celsius setpoints back to the device's Fahrenheit x10 wire representation. Probe-target writes are implemented with readback verification and remain experimental pending a final end-to-end physical write test.

Older development entities for unsupported Wi-Fi/auto-sleep settings are automatically removed from the Home Assistant entity registry.

### TNT-11-B / BG-BT1W

Physically discovered and connected through Home Assistant:

- BLE local name \`BG-BT1W\`;
- model mapped to \`TNT-11-B\`;
- notifications received on FF03;
- live probe temperature exposed in Home Assistant;
- confirmed physical notification \`19 00 18 71\` decodes to **25 °C** from the first signed little-endian 16-bit field.

The remaining bytes in the TNT notification are intentionally kept as raw diagnostics until their meaning is confirmed on physical hardware.

## Coexistence with the INKBIRD app

For Wi-Fi capable models, the intended architecture is:

- Home Assistant owns the BLE connection through a local adapter or ESPHome proxy;
- the INKBIRD app continues to use Wi-Fi/cloud where supported.

This has been physically confirmed on the INT-14-BW. ISC-027BW Wi-Fi/app coexistence and longer running sessions still need further testing.

## Home Assistant entities

The exact entity set depends on the model. Current integration platforms include:

- sensors;
- binary sensors;
- number controls;
- select controls;
- switches.

Configuration/write entities are clearly marked as experimental where the protocol is still being hardware-validated.

## Diagnostics

Home Assistant diagnostics are implemented for troubleshooting. Bluetooth addresses are redacted. Model-specific raw protocol information may be included when useful for protocol validation, such as the TNT-11-B \`raw_packet\` field.

## Development updater

HACS is now the preferred installation/update path for normal testing.

For development branches, protocol work or rollback testing, the repository still includes:

\`scripts/update_inkbird_bbq.sh\`

The updater supports branch/tag selection, backups, \`ha core check\`, rollback on validation failure and an optional Home Assistant restart. See [docs/Updating.md](docs/Updating.md).

## Quality and security checks

Changes are automatically checked with:

- Python compile/syntax validation;
- Ruff linting;
- pytest;
- JSON/YAML validation;
- Home Assistant import smoke tests;
- integration metadata and local brand validation;
- official HACS Validation;
- Bandit;
- pip-audit when external Python requirements are present;
- Gitleaks;
- CodeQL.

## Protocol research and hardware validation

- [Protocol research](docs/PROTOCOL_RESEARCH.md)
- [Hardware validation](docs/Hardware-Validation.md)

## Safety

The ISC-027BW controls combustion airflow. Do not use experimental fan/control writes as the only safety mechanism for a live fire. Validate changes on the bench first and keep the controller's own safety behavior in place.

INT-14-BW target controls also remain experimental until the current Celsius-to-wire conversion has completed final physical set/readback validation.

## Changelog

Development history is tracked in [CHANGELOG.md](CHANGELOG.md).

## License

MIT
