# E700 fault codes

`windrose_dtc_public.csv` — **7,962 fault codes** from the E700 platform: what
each code means, what sets it, what clears it, how serious it is, what the
truck does about it, and where to start looking.

It is the same set the Windrose website assistant answers from.

## Columns

| Column | Meaning |
|---|---|
| `group` | System family: VDC, MCU, IPC, SJB, BMS, PDU, BDCU, EPB, TMS, ADAS, EBS, ECAS, TGW, BODY, CMS, CDCU, EHPS, TPMS, EVCC |
| `ecu` | Controller that reports it |
| `system`, `system_en` | Service-manual section |
| `type` | `UDS` (read with `$19`), `J1939` (DM1 / SPN-FMI), `IPC_warning` (cluster warning), or an internal fault list (`VDC_internal`, `BMS_internal`, …) |
| `code` | Code as a tool shows it, e.g. `B18044B`, `U007388` |
| `hex` | UDS 3-byte DTC, e.g. `0x98044B` (what `$19 02` returns) |
| `spn`, `fmi` | J1939 suspect parameter number and failure mode |
| `name_cn`, `name_en` | Fault name |
| `trigger_cn`, `trigger_en` | Set condition |
| `clear_cn`, `clear_en` | Clear condition |
| `level_cn`, `level_en` | Fault level |
| `reaction_cn`, `reaction_en` | What the vehicle does (power limit, no regen, warning only, …) |
| `troubleshoot_cn`, `troubleshoot_en` | Where to start; section numbers refer to the service manual |
| `en_machine_translated` | `yes` = the English columns were machine-translated from Chinese. Read the Chinese when they disagree |

## How to use it

1. Read the codes from the truck: [`docs/obd.md`](../docs/obd.md), or run
   [`tools/obd_read_all.py`](../tools/obd_read_all.py).
2. Look the code up by `hex` (UDS), by `spn` + `fmi` (J1939), or by `code`.
3. The same code can appear once per controller (for example once for each of
   the four inverters). Match the `ecu` too.

Service manuals, in 20+ languages: https://www.windrose.ai/how-to-service-manuals

## What is not in it

- Which supplier makes which controller, and the suppliers' own diagnostic
  specifications.
- Rows the source lists marked as superseded, reused or misaligned.
- Security access, write, routine and flashing services. Clearing codes is
  not described here.

## Accuracy

Merged from the E700 platform fault lists, the service manual and the cluster
warning list. Software versions differ between trucks; a code your truck
reports may not be listed, and a listed reaction may differ on your software.
Please open an issue when you find one.

## Licence

Apache-2.0, as with the other data in this repository.
