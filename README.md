# INKBIRD BBQ for Home Assistant

Local Home Assistant integration for INKBIRD BBQ controllers and wireless meat thermometers.

> **Development status:** early development. Do not rely on this integration for temperature or fan control yet.

## Initial hardware scope

- INKBIRD ISC-027BW smoker/kamado fan controller
- INKBIRD INT-14-BW wireless meat thermometer
- INKBIRD TNT-11-B wireless meat thermometer

The goal is local Bluetooth communication through Home Assistant's Bluetooth stack, including ESPHome Bluetooth proxies. No cloud dependency is planned for normal Home Assistant operation.

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

English is the base language for code, documentation, entity names, comments, strings, issues, pull requests, and release notes. Dutch Home Assistant translations are maintained alongside the English strings where practical.

## Development policy

The README should be kept up to date with every meaningful change that affects supported hardware, behavior, setup, architecture, safety, roadmap, or installation.

## Current implementation status

The development branch already contains:

- a shared Home Assistant Bluetooth connection layer designed for local adapters and ESPHome Bluetooth proxies;
- automatic Bluetooth discovery for ISC-027BW and INT-14-BW using exact model-name matching;
- model-specific persistent Bluetooth coordinators with reconnect handling;
- a read-only ISC-027BW decoder with frame-length and CRC16-Modbus validation;
- read-only ISC-027BW entities for pit temperature, three wired meat probes, fan output and configured target/alarm temperatures;
- INT-14-BW challenge/response authentication, clock sync and current-state requests;
- read-only INT-14-BW entities for four core temperatures, four ambient temperatures and available battery information;
- protocol unit tests, including a published INT-14-BW authentication test vector;
- English base strings plus an initial Dutch Home Assistant translation;
- protocol provenance and third-party notices.

TNT-11-B automatic discovery is intentionally not implemented yet. Its retail model name is known, but its real BLE advertisement name and protocol family must first be confirmed on the physical device.

Physical hardware is still required before marking any model as validated and before enabling ISC-027BW control writes.

## Protocol research

Public reverse-engineering references, protocol families, licensing notes and hardware validation tasks are tracked in [docs/PROTOCOL_RESEARCH.md](docs/PROTOCOL_RESEARCH.md).

## Roadmap

1. Establish the Home Assistant/HACS integration structure.
2. Implement Bluetooth discovery and read-only coordinators for known models.
3. Capture and validate Bluetooth discovery, services, characteristics and packets on real hardware.
4. Validate reconnect, availability and diagnostics handling through the ESPHome Bluetooth proxy.
5. Confirm app/Wi-Fi/Apple Watch coexistence behavior.
6. Add TNT-11-B support after identifying its actual BLE advertisement and protocol family.
7. Add ISC-027BW controls only after read-only operation is stable and write commands are validated safely.

## Safety

The ISC-027BW controls combustion airflow. Early versions will remain read-only. Fan/setpoint writes will only be enabled after protocol validation and fail-safe behavior are implemented.

## License

MIT
