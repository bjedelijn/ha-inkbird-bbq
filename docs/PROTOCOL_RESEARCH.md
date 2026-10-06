# Protocol research

This document records protocol information used by INKBIRD BBQ for Home Assistant and separates public reverse engineering from behavior confirmed on physical hardware.

## Architecture

The integration uses one Home Assistant domain with independent model drivers:

\`\`\`text
Home Assistant Bluetooth stack / ESPHome proxy
                 |
          connection layer
                 |
       +---------+---------+
       |         |         |
   ISC-027BW  INT-14-BW  TNT-11-B
    driver      driver     driver
       |         |         |
       +---------+---------+
                 |
       HA entities / device model
\`\`\`

Home Assistant's Bluetooth APIs are used rather than direct BlueZ access, allowing Home Assistant to select a local adapter or ESPHome Bluetooth proxy.

## Reference Bluetooth proxy

Development hardware:

- Olimex ESP32-POE-ISO-EA;
- Ethernet + PoE;
- external 2.4 GHz antenna;
- ESPHome Bluetooth Proxy with active connections enabled.

## Coexistence status

| Device | HA via BLE | Vendor app at the same time | Status |
| --- | --- | --- | --- |
| ISC-027BW | Confirmed | Wi-Fi coexistence still to validate | Partial hardware validation |
| INT-14-BW | Confirmed | iPhone app over Wi-Fi confirmed | Partial hardware validation |
| TNT-11-B | Confirmed | Still to validate | Initial hardware validation |

## ISC-027BW

### Public references

Primary BLE reference:

- \`777Timo/inkbird-ble-ha\` (MIT).

Protocol family:

| Characteristic | Direction | Purpose |
| --- | --- | --- |
| FFF1 | Read/write | Fan state/control |
| FFF2 | Read | Temperatures and actual fan output |
| FFF3 | Read/write | Pit target and meat-probe alarm targets |

Known frame behavior:

- 20-byte frames;
- temperature fields use Fahrenheit x10 on the wire;
- CRC16-Modbus covers bytes 0-17 and is stored in bytes 18-19;
- FFF2 carries pit/probe temperatures and actual fan output;
- FFF1 carries fan on/off state;
- FFF3 carries pit and alarm targets.

### Physical confirmation

The tested ISC-027BW advertises as \`S27\` with vendor service FFF0.

Physical hardware confirms:

- telemetry decoding;
- fan state/output;
- target/alarm decoding;
- fan on/off writes;
- pit-target writes;
- probe-alarm writes;
- automatic fan regulation;
- automatic fan shutdown when the pit probe is absent.

The integration therefore does not expose a manual fan-power percentage control.

## INT-14-BW

### Public references

Primary references:

- \`paul43210/inkbird-bw-ble\` (MIT);
- \`boris327/ha-inkbird-int14bw\` (MIT).

Protocol family:

- service FF00;
- FF01 temperature telemetry;
- FF02 authentication, commands and reports;
- FF03 probe/dock state;
- standard 2A19 battery data;
- challenge/response authentication required for a persistent session;
- multi-byte values generally little-endian.

### Physical confirmation

The tested unit advertises as \`INT-14-BW_WH\`.

Confirmed in Home Assistant:

- authentication;
- clock/session setup;
- all four probe channels;
- separate core/ambient temperatures;
- dock state;
- base/probe batteries;
- C/F control;
- display-brightness control;
- BLE reconnect after base power cycle;
- BLE Home Assistant session while the INKBIRD app uses Wi-Fi.

### Target-temperature format

Public reverse engineering showed target report/write support but left the unit boundary uncertain.

Physical observations on this integration showed target values such as 85 and 70 that were actually Fahrenheit values even when they were being presented as Celsius by the earlier decoder.

The current implementation therefore uses:

- target wire value = Fahrenheit x10;
- Home Assistant native value = Celsius;
- read path: Fahrenheit x10 -> Celsius;
- write path: Celsius -> Fahrenheit x10;
- write verification: compare returned raw target with the expected Fahrenheit x10 value.

This behavior is covered by unit tests and still requires a final physical set/readback confirmation before the target controls are considered fully validated.

### Settings scope

Currently exposed INT controls:

- temperature unit;
- display brightness;
- probe target temperatures 1-4.

Earlier experimental Wi-Fi and auto-sleep entities are no longer exposed and are cleaned from the entity registry when encountered from older development builds.

## TNT-11-B / BG-BT1W

### Public references

Independent community implementations identified the TNT-11-B/TempWise family with:

- local name \`BG-BT1W\`;
- service FF01;
- FF03 notification characteristic;
- no mandatory activation sequence for the basic temperature stream.

Some public implementations interpreted the first two bytes as hundredths of a degree. That does not match the tested physical TNT-11-B used for this integration.

### Physical confirmation

The physical device advertises as \`BG-BT1W\`, is discovered as TNT-11-B and successfully streams FF03 notifications.

A captured notification:

\`\`\`text
19 00 18 71
\`\`\`

corresponded to a physical temperature of approximately 25 °C.

For this hardware the confirmed first field is therefore decoded as:

- bytes 0-1;
- signed little-endian 16-bit integer;
- whole degrees Celsius;
- no /100 scaling.

The remaining bytes are kept raw until repeated physical captures identify their semantics.

## Licensing approach

The repository is MIT licensed.

Protocol facts are implemented independently. Where public MIT-licensed projects materially informed behavior, their provenance is documented here and in the repository notices.

The preferred approach is to:

- use public projects as protocol references;
- keep our own Home Assistant architecture and device drivers;
- retain attribution where source code is substantially adapted;
- validate safety-relevant writes on physical hardware.
