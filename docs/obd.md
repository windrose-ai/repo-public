# Reading an E700 through the OBD port

The 16-pin OBD connector under the dash is a **diagnostic** port. The truck
does not stream its internal buses onto it. A gateway sits between the OBD pins
and the vehicle networks. On this plug you mostly get answers by **asking**,
not by listening.

## Lessons from the field

A dealer connected a CAN adapter to the OBD port of a truck that was stopped
with a fault and sent in the recording. The file came back empty. Why it was
empty was not established.

Because the gateway forwards little unprompted traffic to this plug, an empty
or near-empty listen-only recording on the OBD port does not on its own say
anything about the condition of the truck. Before you record, decide whether
you need to **listen** (J1939 broadcast, see below) or to **ask** (UDS). For
fault codes and the VIN, you have to ask.

On another truck, a PEAK adapter opened at classic CAN 500 kbit/s sat at its
bus-error warning limit: about 10,000 error frames in 10 s, and no ECU
answered. Bus errors on this plug point first at the cable-to-adapter wiring
(see "Cable to adapter" below), then at the bus setting.

## The connector

| Pin | Use |
|---|---|
| 6 | Diagnostic CAN high (`GWCANFD9_H`) |
| 14 | Diagnostic CAN low (`GWCANFD9_L`) |
| 16 | Battery + 24 V, always on (do not connect it to your adapter's signal pins) |
| 4, 5 | Ground |
| 3, 11, 12, 13 | Diagnostic Ethernet (DoIP) |

Pins 6 and 14 are the diagnostic CAN segment between the gateway and the OBD
connector (service manual 9.1.49, OBD circuit). The truck already terminates
this segment with 120 Ω: **do not add a terminating resistor** on the adapter
side.

The segment is named a CAN FD bus. Windrose's own UDS reads have used classic
CAN at 500 kbit/s; whether the truck also puts CAN FD frames on it is not yet
confirmed by a recording. `tools/obd_read_all.py` tries classic 500k, CAN FD
500k/2M and classic 250k, listen-only, before it sends anything.

This guide only covers CAN.

### Cable to adapter: check the DB9 pins

OBD-to-DB9 cables and CAN adapters do not use the same DB9 pinout. A common
OBD-to-DB9 cable puts CAN-H on DB9 pin 3 and CAN-L on pin 5; a PEAK PCAN-USB
expects CAN-H on pin 7, CAN-L on pin 2 and ground on pin 3. Plugged straight
together, CAN-H lands on the adapter's ground and the adapter sees only bus
errors at every bit rate.

Check both pinouts before plugging in. If they differ, put two DB9
screw-terminal boards between cable and adapter and wire them across. For an
OBD-to-DB9 cable with CAN-H on 3 and CAN-L on 5, into a PEAK:

| Signal | Cable side (male board) | PEAK side (female board) |
|---|---|---|
| CAN-H | 3 | 7 |
| CAN-L | 5 | 2 |
| Ground | 2 | 3 |
| Signal ground | 1 | 6 |
| Battery + | 9: **leave empty** | 9: **leave empty** |

Never wire OBD pin 16 (battery voltage) to the adapter.

### Check the physical layer with a meter

Before blaming the bus setting, measure at the OBD connector with the adapter
unplugged. These are typical values for a working high-speed CAN bus, not
measurements from an E700:

| Condition | Measure | Typical |
|---|---|---|
| Ignition off | Resistance pin 6 to pin 14 | about 60 Ω (two 120 Ω terminations); about 120 Ω if only one end is terminated |
| Ignition on | Voltage pin 6 to pin 4 | about 2.5–3.5 V |
| Ignition on | Voltage pin 14 to pin 4 | about 1.5–2.5 V |

Open circuit between 6 and 14, or both pins at 0 V with the ignition on, means
the cable, the connector or the segment itself, not the software.

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

### Read everything in one go

[`tools/obd_read_all.py`](../tools/obd_read_all.py) does all of the above,
read-only: it listens for 10 s, asks who is there, reads the identification
DIDs and fault codes from every ECU that answers, sends the J1939 requests, and
saves an `.asc` log plus a text summary. Anything that is not a question is
refused before it reaches the bus.

On Windows, one line in PowerShell does everything, including a private copy
of Python if the laptop has none (no administrator rights needed):

```powershell
irm https://raw.githubusercontent.com/windrose-ai/repo-public/main/tools/obd_read_all.ps1 | iex
```

With Python already installed:

```text
pip install python-can
python obd_read_all.py            # PEAK, finds the bus setting itself
python obd_read_all.py --fd       # force CAN FD 500k / 2M
```

Before it sends anything, the script listens with the adapter in listen-only
mode at classic 500k, CAN FD 500k/2M and classic 250k, and asks only at a
setting that reads the bus without errors. A classic-CAN setting on a CAN FD
bus shows up as a stream of bus errors, not as frames. If every setting gives
bus errors, the script stops without sending and points at the wiring.

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
| Bus errors at every setting (classic 500k, CAN FD, classic 250k) | Wiring: CAN-H / CAN-L swapped or on the wrong DB9 pins, often a cable plugged straight into an adapter with a different pinout. See "Cable to adapter" |
| Bus errors at classic CAN, clean frames at CAN FD | The segment carries CAN FD frames. Use CAN FD 500k/2M |
| Nothing at all, even after a request | Ignition off, the gateway not awake, wrong pins on the cable, or wrong bit rate |
| A few J1939 IDs, no answer to your request | Listening works; check the request ID, the 29-bit setting and the tester address `0xF1` |
| `18DAF1xx` frames after your request | An ECU is answering |
| Negative response `0x33` | That data needs security access. Stop |

## Licence

CC BY 4.0, like the rest of `docs/`.
