# INKBIRD BBQ for Home Assistant

Local Home Assistant integration for INKBIRD BBQ controllers and wireless meat thermometers.

> **Development status:** early skeleton. Do not rely on this integration for temperature or fan control yet.

## Initial hardware scope

- INKBIRD ISC-027BW smoker/kamado fan controller
- INKBIRD INT-14-BW wireless meat thermometer
- INKBIRD TNT-11-B wireless meat thermometer

The goal is local Bluetooth communication through Home Assistant's Bluetooth stack, including ESPHome Bluetooth proxies. No cloud dependency is planned for normal operation.

## Bluetooth proxy recommendation

This integration is designed to use Home Assistant's native Bluetooth stack. A local Bluetooth adapter works, but for a fixed BBQ/kamado setup a dedicated ESPHome Bluetooth proxy is recommended.

Recommended hardware:

- **Olimex ESP32-POE-ISO-EA**
- **BOX-ESP32-POE-ISO-EA-F** enclosure
- Ethernet/PoE connection to the Home Assistant network
- ESPHome Bluetooth Proxy firmware with active Bluetooth connections enabled

Why this hardware is recommended:

- Ethernet avoids sharing the ESP32 radio between Wi-Fi and Bluetooth.
- PoE provides a simple, reliable fixed installation.
- The `-EA` version uses an external antenna, which is useful when the proxy is mounted indoors and the BBQ is outside.
- Home Assistant can automatically route BLE connections through an ESPHome Bluetooth proxy, so the integration itself does not need proxy-specific code.

The proxy should be mounted indoors or in a suitable weatherproof enclosure, reasonably close to the BBQ area and away from access points, switches and other strong RF sources where practical.

## Coexistence with the INKBIRD app and Apple Watch

The integration is intentionally Bluetooth-first while leaving the device's Wi-Fi functionality untouched.

Expected usage for Wi-Fi capable models:

- Home Assistant keeps the local BLE connection through the local adapter or ESPHome Bluetooth proxy.
- The INKBIRD mobile app uses the device's Wi-Fi/cloud path for remote monitoring.
- A phone app must not compete with Home Assistant for the same single active BLE connection.
- For the INT-14-BW, INKBIRD documents Wi-Fi, Bluetooth and Apple Watch monitoring. Community testing also indicates the base can expose a combined Wi-Fi + Bluetooth radio mode.
- The ISC-027BW officially supports both Wi-Fi and Bluetooth. Apple Watch behavior for this specific model still needs hardware/app validation.

This coexistence model is a development goal, not yet a guaranteed feature. It will be tested on the physical devices before release.

## Language policy

English is the base language for code, documentation, entity names, comments, strings, issues, pull requests, and release notes. Additional translations can be added later once the integration behavior and terminology are stable.

## Development policy

The README should be kept up to date with every meaningful change that affects supported hardware, behavior, setup, architecture, safety, roadmap, or installation.

## Current implementation status

The development branch already contains:

- a shared Home Assistant Bluetooth connection layer designed for local adapters and ESPHome Bluetooth proxies;
- a read-only ISC-027BW decoder with frame-length and CRC16-Modbus validation;
- ISC-027BW decoding for pit temperature, three wired meat probes, fan output and configured temperature targets;
- INT-14-BW protocol primitives for discovery, challenge/response authentication, clock sync, FF02 framing, four core/ambient temperature pairs and battery parsing;
- protocol unit tests, including a published INT-14-BW authentication test vector;
- protocol provenance and third-party notices.

The next hardware-independent step is to wire these protocol drivers into model-specific coordinators and Bluetooth discovery. Physical hardware is still required before marking any model as supported or enabling control writes.

## Protocol research

Public reverse-engineering references, protocol families, licensing notes and hardware validation tasks are tracked in [docs/PROTOCOL_RESEARCH.md](docs/PROTOCOL_RESEARCH.md).

English is the project's base language. Dutch Home Assistant translations are maintained alongside the English strings where practical.

## Roadmap

1. Establish the Home Assistant/HACS integration structure.
2. Capture and validate Bluetooth discovery, services, characteristics and packets on real hardware.
3. Implement read-only temperature/status support for each device.
4. Add reliable reconnect, availability and diagnostics handling.
5. Add ISC-027BW controls only after read-only operation is stable and write commands are validated safely.
6. Add translations after behavior and terminology are stable.

## Safety

The ISC-027BW controls combustion airflow. Early versions will remain read-only. Fan/setpoint writes will only be enabled after protocol validation and fail-safe behavior are implemented.

## License

MIT
