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

Confirm:

- advertised local name;
- Bluetooth address format;
- advertised service UUIDs;
- FFF0 service exists;
- FFF1, FFF2 and FFF3 characteristic properties match expectations.

### Read-only telemetry

Check each value against the controller display/app:

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

While Home Assistant owns BLE:

- verify the controller remains connected to Wi-Fi;
- verify the INKBIRD app can still read data over Wi-Fi;
- verify changing views/settings in the app does not steal BLE from Home Assistant;
- verify Apple Watch behavior if the model/app exposes it.

### Control writes

Do **not** enable control entities yet.

Before any write support is merged, separately validate:

- fan on/off encoding;
- manual fan output/setpoint encoding;
- pit target encoding;
- probe alarm target encoding;
- CRC generation;
- acceptable value ranges;
- response/acknowledgement behavior;
- behavior on BLE disconnect during a write;
- behavior on Home Assistant restart;
- safe fallback if Home Assistant is unavailable.

## INT-14-BW validation

### Discovery

Confirm:

- exact advertised local name is `INT-14-BW`;
- FF00 vendor service exists;
- FF01, FF02 and FF03 properties;
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

For each of four probes, validate:

- core/internal temperature;
- ambient temperature;
- probe numbering/order;
- unavailable/sentinel values;
- docked state;
- removal from dock;
- return to dock.

Use deliberately different temperatures per probe so channel mapping is unambiguous.

### Battery reporting

Validate:

- base battery;
- each probe battery if exposed;
- charging/docked behavior;
- invalid/unknown battery values.

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
