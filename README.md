# INKBIRD BBQ for Home Assistant

Local Home Assistant integration for INKBIRD BBQ controllers and wireless meat thermometers.

> **Development status:** early skeleton. Do not rely on this integration for temperature or fan control yet.

## Initial hardware scope

- INKBIRD ISC-027BW smoker/kamado fan controller
- INKBIRD INT-14-BW wireless meat thermometer
- INKBIRD TNT-11-B wireless meat thermometer

The goal is local Bluetooth communication through Home Assistant's Bluetooth stack, including ESPHome Bluetooth proxies. No cloud dependency is planned for normal operation.

## Roadmap

1. Establish the Home Assistant/HACS integration structure.
2. Capture and validate Bluetooth discovery, services, characteristics and packets on real hardware.
3. Implement read-only temperature/status support for each device.
4. Add reliable reconnect, availability and diagnostics handling.
5. Add ISC-027BW controls only after read-only operation is stable and write commands are validated safely.

## Safety

The ISC-027BW controls combustion airflow. Early versions will remain read-only. Fan/setpoint writes will only be enabled after protocol validation and fail-safe behavior are implemented.

## License

MIT
