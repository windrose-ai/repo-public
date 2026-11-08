# Reading an E700 through the OBD port

The 16-pin OBD connector under the dash is a **diagnostic** port. The truck
does not stream its internal buses onto it. A gateway sits between the OBD pins
and the vehicle networks. On this plug you mostly get answers by **asking**,
not by listening.

## Lesson from the field

A dealer connected a CAN adapter to the OBD port of a truck that was stopped
with a fault. They recorded in listen-only mode and sent the file in. The file
came back empty.

An empty listen-only recording on the OBD port is what this design produces when
nobody sends a request. On its own it says nothing about the condition of the
truck. Before you record, decide whether you need to **listen** (J1939
broadcast, see below) or to **ask** (UDS). For fault codes and the VIN, you
have to ask.

## The connector

| Pin | Use |
|---|---|
| 6 | Diagnostic CAN high |
| 14 | Diagnostic CAN low |
| 16 | Battery + (do not connect it to your adapter's signal pins) |
| 4, 5 | Ground |

The same connector also carries diagnostic Ethernet (DoIP). This guide only
covers CAN.

A standard J1962-to-DB9 cable works, but cable makers do not all use the same
DB9 pinout. Check that pins 6 and 14 of the OBD plug land on the CAN-H and
CAN-L pins your adapter expects. Never wire OBD pin 16 (battery voltage) to the
adapter.

## Before you start

- Ignition **on**. With the ignition off, the gateway and most ECUs are asleep
  and nothing answers.
- High-voltage system: follow the vehicle's HV work procedure. Reading over OBD
  does not require opening anything.
- One program per adapter. Close PCAN-View, TSMaster or similar before running
  a script.

## Ask: read-only UDS (fault codes, VIN, versions)

Windrose OBD is **UDS (ISO 14229) over 29-bit CAN identifiers**. It is not
classic OBD-II (J1979 Mode/PID): a generic car OBD-II scanner gets no useful
answer.

| | |
|---|---|
| Bit rate used by Windrose for these reads | Classic CAN, 500 kbit/s |
| Tester address | `0xF1` |
| Physical request to one ECU | `18DA<ecu>F1` |
| Response from that ECU | `18DAF1<ecu>` |
| Functional request (who is there?) | `18DBFFF1` |

**Read-only services you may send**

| Service | What it does |
|---|---|
| `$10 01` / `$10 03` | Default / extended diagnostic session |
| `$22` | ReadDataByIdentifier. Standard DIDs: `F190` VIN, `F187` spare part number, `F18C` serial number, `F193` hardware version, `F195` software version |
| `$19` | ReadDTCInformation (fault codes). Read only |
| `$3E` | TesterPresent, keeps a read session open |

**Do not send:** `$27` SecurityAccess, `$2E` write, `$2F` IO control, `$31`
routines, `$11` reset, `$14` clear fault codes, `$34`–`$37` download or flash.
If an ECU answers a read with a negative response such as `0x33` (security
access denied), stop there. Do not try to unlock it.

### Example with python-can and udsoncan

```text
pip install python-can can-isotp udsoncan
```

```python
import can, isotp, udsoncan
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection

ECU = 0x41  # ask one ECU; use a functional request to find others

bus = can.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=500000)
addr = isotp.Address(isotp.AddressingMode.NormalFixed_29bits,
                     source_address=0xF1, target_address=ECU)
stack = isotp.CanStack(bus, address=addr)
cfg = dict(udsoncan.configs.default_client_config)
cfg['data_identifiers'] = {0xF190: udsoncan.AsciiCodec(17)}

with Client(PythonIsoTpConnection(stack), config=cfg) as client:
    print(client.read_data_by_identifier(0xF190))          # VIN
    print(client.get_dtc_by_status_mask(0xFF))             # fault codes
```

With TSMaster, CANoe or a J2534 PassThru tool, the same rule applies: services
`$10`, `$22`, `$19` and `$3E` only.

## Listen: J1939 broadcast

Some standard J1939 messages are forwarded and can be heard without asking:
vehicle speed and brake state (`CCVS`), accelerator (`EEC2`), gear (`ETC2`),
ABS/EBS state (`EBC1`), collision warning, and some high-voltage battery
summaries.

- Expect tens of CAN IDs, not hundreds.
- A field of all `0xFF` means "not available". It is not a tool failure.
- Use a standard J1939 decoder.

Most of the messages in [`dbc/E700_Open_Telemetry.dbc`](../dbc/) are on the
vehicle's internal buses and are **not** forwarded to the OBD port. Loading that
file into an OBD session will mostly decode nothing.

## Quick check: is it working?

| What you see | What it means |
|---|---|
| Nothing at all, even after a request | Ignition off, wrong pins on the cable, or wrong bit rate |
| A few J1939 IDs, no answer to your request | Listening works; check the request ID, the 29-bit setting and the tester address `0xF1` |
| `18DAF1xx` frames after your request | An ECU is answering |
| Negative response `0x33` | That data needs security access. Stop |

## Licence

CC BY 4.0, like the rest of `docs/`.
