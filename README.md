# INKBIRD BBQ for Home Assistant

Local Home Assistant integration for INKBIRD BBQ controllers and wireless meat thermometers.

> **Development status:** early skeleton. Do not rely on this integration for temperature or fan control yet.

## Initial hardware scope

- INKBIRD ISC-027BW smoker/kamado fan controller
- INKBIRD INT-14-BW wireless meat thermometer
- INKBIRD TNT-11-B wireless meat thermometer

The goal is local Bluetooth communication through Home Assistant's Bluetooth stack, including ESPHome Bluetooth proxies. No cloud dependency is planned for normal operation.

## Language policy

English is the base language for code, documentation, entity names, comments, strings, issues, pull requests, and release notes. Additional translations can be added later once the integration behavior and terminology are stable.

## Development policy

The README should be kept up to date with every meaningful change that affects supported hardware, behavior, setup, architecture, safety, roadmap, or installation.

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
