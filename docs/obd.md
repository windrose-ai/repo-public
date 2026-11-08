# Reading an E700 through the OBD port

The 16-pin OBD connector under the dash is a **diagnostic** port. The truck
does not stream its internal buses onto it. A gateway sits between the OBD pins
and the vehicle networks. On this plug you mostly get answers by **asking**,
not by listening.

## Lesson from the field

A dealer connected a CAN adapter to the OBD port of a truck that was stopped
with a fault and sent in the recording. The file came back empty. Why it was
empty was not established.

Because the gateway forwards little unprompted traffic to this plug, an empty
or near-empty listen-only recording on the OBD port does not on its own say
anything about the condition of the truck. Before you record, decide whether
you need to **listen** (J1939 broadcast, see below) or to **ask** (UDS). For
fault codes and the VIN, you have to ask.

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
| Bit rate | Classic CAN, 500 kbit/s (Windrose's setting for these reads; if nothing answers, the segment may be CAN FD, 500 kbit/s arbitration and 2 Mbit/s data) |
| Tester address | `0xF1` |
| Physical request to one ECU | `18DA<ecu>F1` |
| Response from that ECU | `18DAF1<ecu>` |
| Functional request (who is there?) | `18DBFFF1` |

## What you can ask

### Read-only UDS services

| Service | What it does |
|---|---|
| `$10 01` / `$10 03` | Default / extended diagnostic session. Stay in `01` if the read works there |
| `$22` | ReadDataByIdentifier (see the DID table) |
| `$19` | ReadDTCInformation: fault codes and their status |
| `$3E` | TesterPresent, keeps a read session open |

**Data identifiers for `$22`** (ISO 14229 standard identification DIDs)

| DID | What comes back |
|---|---|
| `F190` | VIN |
| `F187` | Spare part number |
| `F18C` | ECU serial number |
| `F193` | Hardware version |
| `F195` | Software version |
| `F1A1` | Vehicle configuration, where the ECU implements it |
| `F010` | Cabin domain controller (CDCU) only: end-of-line option bitmap. Read only |

Not every ECU implements every DID. A negative response `0x31` (request out
of range) means that ECU does not have it. Move on.

**Fault codes with `$19`**

| Sub-function | Request | What comes back |
|---|---|---|
| `01` | `19 01 FF` | How many fault codes match the status mask |
| `02` | `19 02 FF` | The fault codes and the status byte of each |
| `0A` | `19 0A` | Every fault code the ECU supports, with status |
| `04` | `19 04 <DTC> FF` | Freeze-frame (snapshot) data for one code, where stored |
| `06` | `19 06 <DTC> FF` | Extended data (counters) for one code, where stored |

Send the codes, with the ECU name and the VIN, to Windrose. Windrose maps them
to descriptions; the code list is not published here.

### Which ECUs to ask

Send `18DBFFF1` (functional) first: every ECU that is awake answers, and the
answers tell you which addresses are present. The main ones for service:

| ECU | Address | Request ID | Response ID |
|---|---|---|---|
| Gateway | `FB` | `18DAFBF1` | `18DAF1FB` |
| Powertrain domain controller (VDC) | `27` | `18DA27F1` | `18DAF127` |
| Body domain controller (BDCU) | `21` | `18DA21F1` | `18DAF121` |
| Cabin domain controller (CDCU) | `41` | `18DA41F1` | `18DAF141` |
| Instrument cluster | `17` | `18DA17F1` | `18DAF117` |
| Inverters 1–4 | `74`–`77` | `18DA74F1` … `18DA77F1` | `18DAF174` … `18DAF177` |
| Transmission | `03` | `18DA03F1` | `18DAF103` |
| Battery domain | `A6` | `18DAA6F1` | `18DAF1A6` |
| HV distribution (PDU) | `78` | `18DA78F1` | `18DAF178` |
| Brakes (EBS) | `0B` | `18DA0BF1` | `18DAF10B` |
| Park brake (EPB) | `50` | `18DA50F1` | `18DAF150` |
| Air suspension (ECAS) | `2F` | `18DA2FF1` | `18DAF12F` |
| Smart junction box, upper / under | `54` / `59` | `18DA54F1` / `18DA59F1` | `18DAF154` / `18DAF159` |
| HVAC | `19` | `18DA19F1` | `18DAF119` |

Addresses come from the E700 communication matrix. Regional variants can
differ; trust what the functional request returns on the truck in front of
you. Bought-in brake, suspension and steering ECUs answer identification and
fault-code reads; their deeper diagnostics belong to their suppliers.

### Read-only J1939 requests

On the same plug you can also send a J1939 Request (PGN 59904) from an
off-board tool address (for example `0xF9`) for one of these:

| Ask for | PGN | What comes back |
|---|---|---|
| DM1 | 65226 | Active fault codes (SPN, FMI, count) |
| DM2 | 65227 | Previously active fault codes |
| DM4 | 65229 | Freeze-frame parameters |
| DM5 | 65230 | Diagnostic readiness |
| DM6 | 65231 | Pending fault codes |
| DM12 | 65236 | Emissions-related active fault codes |
| VI | 65260 | VIN |
| CI | 65259 | Component identification |
| SOFT | 65242 | Software identification |

**Never request DM3 (65228) or DM11 (65235).** Both clear fault codes.

### Do not send

`$27` SecurityAccess, `$2E` write, `$2F` IO control, `$31` routines, `$11`
reset, `$14` clear fault codes, `$28` communication control, `$85` DTC setting
control, `$34`–`$37` download or flash, J1939 DM3 / DM11, and any command or
periodic frame. If an ECU answers a read with a negative response such as
`0x33` (security access denied), stop there. Do not try to unlock it.

None of the addresses above has yet been confirmed by a logged read on a
customer truck. If you read one, Windrose would like the log.

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
