# Protocol research

This document records public protocol research used while developing INKBIRD BBQ for Home Assistant. It intentionally separates observed/documented protocol facts from behavior that still needs validation on our own hardware.

## Design decision

The integration uses one Home Assistant domain with independent device protocol drivers. The supported devices do not share one wire protocol, even though they share the INKBIRD brand and BBQ use case.

## Bluetooth transport and proxy

The integration must use Home Assistant's Bluetooth APIs rather than connecting directly to BlueZ. This allows Home Assistant to select the best available Bluetooth path, including remote ESPHome Bluetooth proxies.

The reference proxy for development and testing is:

- **Olimex ESP32-POE-ISO-EA**
- Ethernet + PoE
- external 2.4 GHz antenna
- ESPHome Bluetooth Proxy with active connections enabled
- optional **BOX-ESP32-POE-ISO-EA-F** enclosure

The integration must not assume that the Bluetooth controller is local to the Home Assistant host. Connection, reconnect and discovery behavior will therefore be tested through the Olimex proxy as the primary development path.

The proxy is a transport component only. Device protocol logic remains in the model-specific drivers.

## ISC-027BW

### Public BLE research

Reference: [777Timo/inkbird-ble-ha](https://github.com/777Timo/inkbird-ble-ha) (MIT, Copyright 2026 Timo Prager).

Documented characteristics:

| Characteristic | Direction | Documented purpose |
| --- | --- | --- |
| FFF1 | Read/write | Fan state/control |
| FFF2 | Read/notify | Four temperatures and actual fan output |
| FFF3 | Read/write | Grill target and meat-probe alarm targets |

Documented frame properties:

- Frames are 20 bytes.
- Temperature values are unsigned little-endian Fahrenheit x10.
- CRC16-Modbus is calculated over bytes 0-17 and stored in bytes 18-19.
- FFF2 bytes 0-7 contain four temperature values; byte 8 contains actual fan output in percent.
- FFF1 byte 0 represents fan on/off; byte 6 has been documented as fan speed setpoint.
- FFF3 contains grill target temperature and probe alarm targets.

### Independent Wi-Fi/Tuya research

Two public projects also document the ISC-027BW over its Wi-Fi/Tuya path. These are useful as a cross-check for device capabilities, alarms, targets and fan behavior, but the initial integration will use Bluetooth through Home Assistant's Bluetooth stack.

### Validation required

Before enabling writes we will verify on our physical unit:

- advertised name and service UUIDs;
- exact FFF1/FFF2/FFF3 lengths and properties;
- CRC byte order;
- temperature conversion and invalid/sentinel values;
- fan state and fan-output semantics;
- target-temperature encoding;
- probe alarm offsets;
- reconnect behavior through an ESPHome Bluetooth proxy;
- behavior after power loss, BLE loss and Home Assistant restart.

Writes remain disabled until these checks pass.

## INT-14-BW

### Public protocol research

Primary references:

- [paul43210/inkbird-bw-ble](https://github.com/paul43210/inkbird-bw-ble) (MIT, Copyright 2026 Paul Faure)
- [boris327/ha-inkbird-int14bw](https://github.com/boris327/ha-inkbird-int14bw) (MIT, Copyright 2026 Boris Pustilnik)

Documented protocol family:

- vendor service FF00;
- FF01 carries temperature telemetry;
- FF02 carries authentication, commands and state;
- FF03 carries probe/dock state;
- standard 2A19 is used for battery data;
- a fresh challenge/response authentication is required for a persistent session;
- FF02 frames use a length byte followed by a type and payload;
- multi-byte values are generally little-endian.

The public research includes a reference implementation and test vectors for the challenge/response algorithm. We should port the protocol behavior into our own driver and retain required MIT attribution for any source code that is substantially reused.

### Validation required

On our physical INT-14-BW we will verify:

- advertised name/address and discovery behavior;
- four-probe telemetry layout for our firmware;
- core and ambient temperature offsets;
- dock/charging state;
- base and probe battery reporting;
- authentication test vectors and live handshake;
- reconnect/backoff behavior through the Olimex ESPHome Bluetooth proxy;
- single-central limitation when the INKBIRD phone app is connected.

## TNT-11-B

No protocol assumptions will be committed yet. When the device arrives we will capture:

1. advertisement name and manufacturer/service data;
2. GATT services and characteristic properties;
3. notifications while inserting/removing/heating the probe;
4. battery behavior;
5. whether authentication is required;
6. whether it belongs to the same FF00/auth family as other recent INKBIRD thermometers.

## Licensing approach

Our repository is MIT licensed. The main protocol references listed above are also MIT licensed. Protocol facts can be independently implemented. If we copy or substantially adapt source code from an MIT project, its copyright and permission notice must be retained in the relevant distribution/source context.

For clarity and maintainability, the preferred approach is:

- use public projects as protocol references;
- write our own device-driver structure and Home Assistant integration code;
- reuse small protocol algorithms only where that reduces risk, with explicit attribution;
- document provenance here;
- validate all safety-relevant control behavior on our own hardware.

## Planned driver boundary

```
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
```

This keeps connection/retry behavior reusable while protocol parsing and commands remain model-specific.
