# Hardware validation

This document records physical validation of the supported INKBIRD models.

The primary development transport is an **Olimex ESP32-POE-ISO-EA** running ESPHome Bluetooth Proxy over Ethernet/PoE. A local Home Assistant Bluetooth adapter can also be used.

## Current status

| Model | Discovery | Read path | Write/control path | Remaining work |
| --- | --- | --- | --- | --- |
| ISC-027BW | Confirmed | Confirmed | Fan on/off, pit target and probe alarms confirmed | Long-run/restart and app coexistence testing |
| INT-14-BW | Confirmed | Confirmed | C/F, brightness and probe targets confirmed | Long-run/soak testing |
| TNT-11-B | Confirmed | Probe temperature confirmed | No writes | Decode remaining notification bytes and perform broader temperature/reconnect tests |

## General preparation

Before a physical test:

1. install the current integration version;
2. confirm Home Assistant sees a connectable Bluetooth adapter or ESPHome proxy;
3. confirm the test device is advertising;
4. enable debug logging only when protocol data is required;
5. keep safety-relevant blower testing off a live fire.

Optional logger configuration:

\`\`\`yaml
logger:
  logs:
    custom_components.inkbird_bbq: debug
\`\`\`

## Bluetooth proxy

Reference hardware:

- Olimex ESP32-POE-ISO-EA;
- BOX-ESP32-POE-ISO-EA-F;
- external 2.4 GHz antenna;
- PoE/Ethernet;
- ESPHome Bluetooth Proxy with active connections enabled.

Still useful to validate across all models:

- proxy restart recovery;
- Home Assistant restart recovery;
- long-running BLE sessions;
- behavior when multiple Bluetooth paths are available.

## ISC-027BW

### Confirmed discovery

Physical hardware advertises as:

- local name: \`S27\`;
- connectable: yes;
- vendor service: FFF0.

### Confirmed telemetry

Home Assistant physically reads:

- pit temperature;
- meat probes 1-3;
- fan output percentage;
- fan running state;
- pit target;
- probe alarm targets 1-3.

Frames are checked with CRC16-Modbus before decoding.

### Confirmed writes

Physical bench testing confirms:

- fan on/off;
- pit target changes;
- probe alarm target changes;
- immediate readback after writes.

The fan output percentage is automatically regulated by the ISC-027BW and is not exposed as a user-settable power control. The controller also disables the fan when the grill/pit probe is absent.

### Remaining ISC work

- long-running test session;
- recovery after proxy restart;
- recovery after Home Assistant restart;
- Wi-Fi/INKBIRD-app coexistence;
- safe behavior during BLE loss while a write is in progress.

## INT-14-BW

### Confirmed discovery and session

Physical hardware:

- advertises as \`INT-14-BW_WH\`;
- is connectable;
- advertises vendor service FF00;
- completes challenge/response authentication;
- maintains a persistent session through the Olimex proxy.

### Confirmed telemetry

Physically validated:

- probes 1-4 dock/undock state;
- probes 1-4 core temperature;
- probes 1-4 ambient temperature;
- base battery;
- probes 1-4 battery values;
- reconnect after power cycling the base.

Docked probes are exposed as unavailable for temperature.

### Confirmed controls

Physical testing confirms:

- temperature unit C/F, including C -> F -> C;
- display brightness;
- probe target writes for all four probes;
- target values match both the physical base and the INKBIRD app.

Wi-Fi and auto-sleep controls from earlier development builds are no longer exposed. The official app did not provide a usable auto-sleep adjustment path during testing, and a Wi-Fi toggle is not required for the intended coexistence model.

### Probe target temperatures

Target reports are available per probe.

Physical observations showed values that were Fahrenheit while Home Assistant had previously labelled them as Celsius. The current driver therefore treats the target wire value as **Fahrenheit x10**, converts it to Celsius for Home Assistant, and converts Celsius setpoints back to Fahrenheit x10 for the device.

Examples:

- raw \`850\` = 85 °F = approximately 29.4 °C;
- 70 °C encodes to 158 °F = raw \`1580\`.

Target controls for probes 1-4 use immediate readback verification and are now physically validated. Setting a Celsius target in Home Assistant produces the matching value on the physical base and in the INKBIRD app. Switching C -> F -> C preserves the target correctly.

The target number entities follow the device display unit in Home Assistant: °C in Celsius mode and °F in Fahrenheit mode. The coordinator continues to keep a normalized Celsius value internally and converts at the entity/wire boundaries.

Temperature unit and display brightness are requested immediately after authentication, with direct FF02 readback/retry, so their Home Assistant controls populate from the current device state instead of initially remaining unknown.

### Connectivity and coexistence

Confirmed:

- base power-cycle reconnect;
- reconnect after ESPHome Bluetooth Proxy restart;
- reconnect after Home Assistant restart;
- Home Assistant owns BLE while the INKBIRD iPhone app continues over Wi-Fi.

Recommended phone setup for Wi-Fi-capable models:

- allow the INKBIRD app to use its Wi-Fi/cloud path;
- deny Bluetooth permission to the INKBIRD app when Bluetooth is not needed by the app;
- let Home Assistant remain the sole BLE client through the local adapter or ESPHome Bluetooth proxy.

This avoids the phone app competing with Home Assistant for a single BLE session. Do not use this recommendation for a Bluetooth-only model unless the app is known to work without Bluetooth.

Still useful to validate:

- a full long-running cook/test session;
- Apple Watch coexistence if relevant.

## TNT-11-B / BG-BT1W

### Confirmed discovery

Physical device:

- retail model: TNT-11-B;
- BLE local name: \`BG-BT1W\`;
- connectable through Home Assistant;
- FF01 protocol family;
- FF03 notifications provide live data.

Automatic discovery is enabled for \`BG-BT1W\`.

### Confirmed temperature field

A real diagnostic notification was:

\`\`\`text
19 00 18 71
\`\`\`

The first two bytes are interpreted as a signed little-endian integer in whole degrees Celsius:

\`19 00\` -> \`0x0019\` -> **25 °C**

This corrected an earlier experimental decoder that divided the value by 100 and incorrectly displayed 0.25 °C.

Home Assistant now exposes this confirmed field as the TNT-11-B probe temperature.

### Remaining TNT work

The bytes after the first two temperature bytes are retained as \`raw_packet\` diagnostics and are not assigned a meaning yet.

Continue physical capture at several known temperatures to determine:

- whether byte 2 contains a second/ambient temperature or another field;
- battery/state encoding;
- behavior during rapid warming/cooling;
- negative/low-temperature representation if applicable;
- reconnect after device/proxy/Home Assistant restart;
- behavior when the vendor app connects.

No TNT write controls are currently exposed.

## Acceptance criteria

A model can be considered fully hardware validated when:

- discovery is model-specific and repeatable;
- every exposed value matches the physical display/app;
- invalid/absent probe states are handled safely;
- reconnect is reliable;
- Home Assistant restart recovery works;
- diagnostics are useful without exposing unnecessary identifiers;
- app coexistence behavior is documented where relevant;
- all repository CI, Security, CodeQL and HACS validation checks remain green.

Safety-relevant write paths require explicit physical validation beyond unit tests.
