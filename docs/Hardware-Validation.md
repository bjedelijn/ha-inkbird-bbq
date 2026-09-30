# Hardware validation plan

This checklist is used before any supported model is marked as hardware-validated.

The primary development transport is an **Olimex ESP32-POE-ISO-EA** running ESPHome Bluetooth Proxy over Ethernet/PoE. A local Home Assistant Bluetooth adapter may also be used for comparison.

## General preparation

Before testing a device:

1. update Home Assistant to the intended test version;
2. install the current INKBIRD BBQ development branch;
3. confirm `ha core check` passes;
4. confirm the ESPHome Bluetooth proxy is online in Home Assistant;
5. place the proxy in its intended indoor location near the BBQ area;
6. close the INKBIRD mobile app or ensure it is using Wi-Fi rather than holding the BLE connection;
7. enable debug logging for the integration only when required.

Recommended logger configuration:

```yaml
logger:
  logs:
    custom_components.inkbird_bbq: debug
```

## Bluetooth proxy

Reference hardware:

- Olimex ESP32-POE-ISO-EA
- BOX-ESP32-POE-ISO-EA-F
- external 2.4 GHz antenna
- PoE/Ethernet
- ESPHome Bluetooth Proxy with active connections enabled

Validate:

- Home Assistant sees the proxy as available;
- active Bluetooth connections are enabled;
- advertisements from the test device are visible;
- the device can be connected through the proxy;
- reconnect works after device power cycle;
- reconnect works after proxy restart;
- reconnect works after Home Assistant restart;
- moving the phone in/out of BLE range does not unexpectedly steal the connection when the vendor app is using Wi-Fi.

## ISC-027BW validation

### Discovery

Confirmed on physical hardware through the Olimex ESPHome Bluetooth proxy:

- advertised local name is `S27`;
- advertisement is connectable;
- vendor service UUID FFF0 is advertised;
- manufacturer data is present.

Continue to verify after connecting:

- FFF0 service exists in GATT;
- FFF1, FFF2 and FFF3 characteristic properties match expectations.

### Read-only telemetry

Initial physical connection through the Olimex proxy is confirmed. With the current bench setup, Home Assistant successfully read:

- pit target: 107.2 °C;
- fan running: off;
- fan output: 0%;
- three probe alarm targets: 310.0 °C.

The live pit/probe temperatures were unknown during this observation. Continue by checking each value against the controller display/app:

- pit temperature;
- meat probe 1;
- meat probe 2;
- meat probe 3;
- fan output percentage;
- fan running state;
- pit target;
- each meat-probe alarm target.

Test at several temperatures, including room temperature and a warmed probe.

### Invalid and absent probes

Verify behavior when:

- a wired probe is unplugged;
- a probe is reinserted;
- a target/alarm is disabled;
- the controller is idle;
- the blower is physically disconnected.

No invalid sentinel value may appear as a plausible temperature.

### Connectivity

Verify:

- clean initial connection;
- power-cycle recovery;
- BLE loss and reconnect;
- proxy restart;
- Home Assistant restart;
- long-running connection for at least one complete cook/test session.

### Wi-Fi/app coexistence

Confirmed for the INT-14-BW: Home Assistant owns the BLE connection through the Olimex proxy while the INKBIRD iPhone app remains connected to the controller over Wi-Fi. The HA values continued to update during this test.

Still validate:

- the same coexistence behavior on the ISC-027BW;
- whether opening the app can ever seize the BLE session;
- Apple Watch behavior.

### Fan behavior confirmed

Physical testing confirms that the ISC-027BW fan power is automatically regulated. The BLE control can switch the fan on/off, while FFF2 reports the actual automatic fan output percentage. The controller also switches the fan back off when the grill/pit probe is absent.

The fan-power number control is therefore not exposed in Home Assistant.

### Experimental control writes

Experimental entities are included for bench validation and are **disabled by default**. Do not connect the blower to a live fire while validating writes.

Validate in this order:

1. pit target: change a small amount, confirm the controller display/app changes, then restore it;
2. one probe alarm target: change, confirm, restore;
3. blower physically disconnected from the kamado: fan on/off;
4. reconnect the grill probe and confirm the ISC automatically regulates fan output; actual output is read from FFF2 and is not user-adjustable;
5. verify every write is reflected by the immediate FFF1/FFF3 readback;
6. power-cycle and confirm the final values persist or reset exactly as the controller documents.

Also validate:

- CRC generation;
- acceptable value ranges;
- response/acknowledgement behavior;
- behavior on BLE disconnect during a write;
- behavior on Home Assistant restart;
- safe fallback if Home Assistant is unavailable.

These controls must remain disabled by default until this sequence is complete.

## INT-14-BW validation

### Discovery

Confirmed on physical hardware through the Olimex ESPHome Bluetooth proxy:

- advertised local name is `INT-14-BW_WH`;
- advertisement is connectable;
- vendor service UUID FF00 is advertised;
- manufacturer data and service data are empty in the observed advertisement.

Continue to verify:

- FF01, FF02 and FF03 properties after connecting;
- standard battery characteristic 2A19 behavior.

Look-alike models such as INT-14S-BW or INT-12I-BW must not be matched automatically.

### Authentication

Capture and verify:

- challenge request `01 FB`;
- six-byte fresh challenge;
- generated verify response;
- successful FC acknowledgement;
- clock-sync acceptance;
- persistent connection beyond the unauthenticated disconnect window.

### Probe telemetry

Confirmed on physical hardware:

- all four dock states are reported correctly while probes are in the charging station;
- docked probes are exposed as unavailable/unknown for temperature;
- removing probe 1 changes its dock state immediately;
- probe 1 then reports both core and ambient temperature;
- first room-temperature observation reported 23.0 °C core and 23.0 °C ambient.

Additional physical validation:

- returning probe 1 to the charging station restores the docked state and its temperature entities return to unavailable/unknown;
- removing probe 2 correctly changes probe 2 to undocked;
- probe 2 reported 27.0 °C core and 24.0 °C ambient during the test, confirming separate core/ambient offsets and probe 2 channel mapping.

Additional physical validation:

- probe 3 undock/dock state is mapped correctly and reported 24.0 °C core / 24.0 °C ambient while undocked;
- probe 4 undock/dock state is mapped correctly and reported 24.0 °C core / 24.0 °C ambient while undocked;
- all four physical probe channels now map to their matching Home Assistant entities.

Still validate:

- deliberately different temperatures on probes 3 and 4 if a final cross-channel stress check is desired;
- unavailable/sentinel values beyond normal docking behavior.

### Read-only settings

The integration requests the following settings over FF02 after authentication. Each request is sent separately; because two physical tests still left these values unavailable, the driver also reads FF02 after every request and retries missing settings every 30 seconds:

- temperature unit;
- target report for probes 1-4;
- display brightness;
- volume/mute raw report;
- Wi-Fi enabled state;
- auto-sleep.

The first combined-read implementation and the second individual-write implementation both created the entities but left these values unavailable on the physical unit. Re-test the readback/retry path against the physical display/app:

- temperature unit;
- display brightness;
- Wi-Fi enabled;
- auto-sleep minutes.

For target temperature, compare the captured raw value in diagnostics/debug logging with the app/display before exposing it as a temperature entity. The public protocol research still leaves the C/F scaling boundary unresolved for target writes.

Target-temperature and volume writes remain disabled because their encoding/scaling is not sufficiently validated.

### Experimental INT-14-BW setting writes

Experimental setting controls are included but disabled by default. Validate them one at a time:

1. temperature unit: C → F → C and confirm the base display changes;
2. brightness: 100% → 50% → 100%;
3. auto-sleep: set a small test value, confirm, then restore;
4. Wi-Fi switch only after the other controls pass, because it can intentionally disconnect the base from Wi-Fi.

After each write, confirm both the physical display/app and the FF02 readback/debug data. Do not enable INT-14-BW target-temperature writes until the target scaling question is resolved.

### Battery reporting

Confirmed on physical hardware:

- base battery is exposed in Home Assistant;
- battery values for all four probes are exposed;
- first observed values were 99% for the base and 100% for each probe.

Still validate:

- charging behavior over time;
- changing battery values;
- invalid/unknown battery values.

### Connectivity

Confirmed on physical hardware through the Olimex proxy:

- when the INT-14-BW base station was powered off, Home Assistant lost the device data as expected;
- after the base station was powered back on and resumed Bluetooth advertising, the integration automatically reconnected without manual intervention;
- battery, dock-state and temperature values resumed after reconnect.

Still validate:

- ESPHome proxy restart recovery;
- Home Assistant restart recovery;
- a longer running session.

### Wi-Fi/app/Watch coexistence

With Home Assistant connected over BLE:

- keep the base on Wi-Fi;
- verify the INKBIRD app can monitor over Wi-Fi;
- verify Apple Watch monitoring;
- confirm opening the phone app does not seize the BLE session when Wi-Fi monitoring is available.

Also test the reverse order: app first, then Home Assistant.

## TNT-11-B discovery session

No protocol is assumed yet.

Record:

- advertised local name;
- address;
- manufacturer data;
- service UUIDs;
- all GATT services and characteristic properties;
- battery service behavior;
- notifications with the probe cold, warm and changing temperature;
- behavior when the phone app connects;
- whether authentication is required;
- whether its protocol resembles the FF00/auth family.

Only after this capture should automatic discovery and a model driver be added.

## Acceptance criteria

A model can move from **experimental** to **hardware validated** only when:

- automatic discovery is correct and model-specific;
- all exposed read-only entities match the physical device/app;
- invalid probe states are handled safely;
- reconnect is reliable through the Olimex proxy;
- Home Assistant restart recovery works;
- diagnostics contain enough information to investigate failures without exposing unnecessary identifiers;
- app/Wi-Fi coexistence behavior is documented;
- CI remains green.

ISC-027BW control entities require a separate write-safety validation before they can be enabled.
