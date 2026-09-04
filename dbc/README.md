# E700 Open Telemetry — CAN database

`E700_Open_Telemetry.dbc` — **48 messages · 458 signals · 40 KB plain text**

The read channel of the Windrose E700: every signal the vehicle broadcasts about
its own state, and nothing that commands it.

## What a DBC is

A CAN bus carries unlabelled numbers. Without a database file, the wire says:

```
18012774   00 10 DC 05 20 03 64 2A
```

With one, the same frame reads: motor speed −15,250 rpm · actual torque
−2,920 N·m · IGBT gate OFF · HV loop OK · fault class 2.

The DBC records which CAN ID is which message, which bits inside are which
signal, the scaling and the unit. Plain text, understood by every CAN tool.

## Scope — read only, by design

**Included — what the vehicle says about itself**

| Domain | Messages | Signals |
|---|---:|---:|
| Battery — cell voltages, temperatures, SOC, pack current | 3 | 109 |
| Motor & inverter — speed, torque, phase current, temperatures | 16 | 92 |
| Vehicle state — speed, odometer, gear, ratio, hours | 10 | 88 |
| Gearbox — output shaft speed, shift status, fault registers | 10 | 69 |
| HV distribution & insulation resistance | 2 | 40 |
| Brakes & individual wheel speeds | 3 | 29 |
| Vehicle alarm bitmap | 1 | 19 |
| Thermal management | 3 | 12 |
| **Total** | **48** | **458** |

**Deliberately excluded — the write path**

- Command messages — torque, speed, direction, gate and gear commands
- Diagnostic services, security access, flashing routines
- Checksum and rolling-counter definitions — 42 such signals were removed
- Third-party supplier diagnostic specifications — not ours to publish

*Reading a vehicle never changes it. Commanding one does. This file is the read
half, and the split is the point: the boundary sits at the ability to command,
not at the ability to observe.*

## Rates

| | |
|---|---|
| Signal values per second | ≈ 19,700 |
| Fastest message | 10 ms — **100 Hz** (motor and gearbox state) |
| Messages at 20 ms or faster | 22 of 48 |
| On-wire volume if everything is logged | ≈ 40 KB/s → 140 MB per hour |

## Portability — 11 of the 48 work on any truck

Eleven messages are standard SAE J1939 and carry 57 of the signals. A **PGN**
(Parameter Group Number) is J1939's catalogue number for a standard message, so
these decode on **any J1939 commercial vehicle**, from any manufacturer:

| Message | PGN | Period | What it carries |
|---|---|---|---|
| `EBC1` | 61441 | 100 ms | ABS and traction control flags, brake pedal position, retarder |
| `ETC1` | 61442 | 10 ms | Input and output shaft speed, driveline engaged, shift in process |
| `EEC2` | 61443 | 50 ms | Accelerator position, low-idle switch, percent load |
| `EEC1` | 61444 | 20 ms | Actual and demanded percent torque, motor speed |
| `ETC2` | 61445 | 100 ms | Selected gear, current gear, actual gear ratio |
| `TCO1` | 65132 | 50 ms | Vehicle speed, output shaft speed |
| `HRW` | 65134 | 20 ms | All four wheel speeds, individually |
| `EBC2` | 65215 | 50 ms | Front axle speed, per-wheel relative speed on three axles |
| `VDHR` | 65217 | 1 s | Total and trip distance, high resolution |
| `EEC3` | 65247 | 250 ms | Nominal friction torque, estimated parasitic losses |
| `CCVS` | 65265 | 100 ms | Wheel-based speed, park brake, brake switch, cruise, PTO |

The other 37 messages and 401 signals are Windrose message IDs and bit layouts.
They decode nothing on another manufacturer's vehicle — and by the same token,
nothing here is a security concern for anybody else's product.

## Bus

Classic CAN at 500 kbit/s, and CAN FD (500 kbit/s arbitration, 2 Mbit/s data).
CAN FD messages cannot be received by classic-CAN-only hardware.

## Using it

```python
import cantools, can

db  = cantools.database.load_file('E700_Open_Telemetry.dbc')
bus = can.Bus(channel='can0', interface='socketcan')   # listen-only

for msg in bus:
    try:
        print(db.decode_message(msg.arbitration_id, msg.data))
    except KeyError:
        pass
```

Works with SavvyCAN, BusMaster, CANoe, TSMaster, `python-can` + `cantools`.
Validated against `cantools`.

> **Configure the interface in listen-only / silent mode.** This database
> describes a read channel; a tool that transmits on a live vehicle bus can
> disturb it regardless of what it sends. High-voltage system — follow the
> vehicle's HV work procedure.

## Accuracy

Generated from the E700 platform communication matrix. Regional variants share
the great majority of it; charging, some driver assistance and regional
telematics differ. Verify market-specific messages against the vehicle in front
of you, and please open an issue if you find a discrepancy.

## Licence

Apache-2.0, as with everything else in this repository. Use it, redistribute it,
build products on it.
