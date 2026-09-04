# Windrose E700 — Open Documentation & Engineering Data

Windrose builds long-haul battery-electric semi trucks. This repository publishes
engineering documentation and data for the **E700** (type WH13-A, EU-homologated
6×4 battery-electric N3 tractor) in the spirit of the open-source movement, to
help accelerate the adoption of electric truck technology.

> Everything here is free to use. Full manuals — service, owner, warranty and
> maintenance, in 20+ languages — are published on the Windrose website:
> **https://www.windrose.ai/how-to-service-manuals**

## What's in this repository

| Path | Contents |
|---|---|
| [`dbc/`](dbc/) | **CAN database — the E700 read channel.** 48 messages, 458 signals: battery, motor, gearbox, brakes, insulation, vehicle state |
| [`docs/`](docs/) | Interface documentation (ADAS control interface) |

### What we publish, and what we do not

The CAN database is split by **direction of information flow**, not by document.

- **Published — the read channel.** Everything the vehicle broadcasts about its
  own state: speeds, torques, currents, temperatures, state of charge,
  insulation resistance, gear, distance, fault status.
- **Not published — the write path.** Command messages, diagnostic and flashing
  services, security access, and the checksum and rolling-counter definitions
  that make a forged command acceptable.
- **Not ours to publish.** Diagnostic specifications for bought-in brake,
  suspension and steering electronics belong to those suppliers and are covered
  by technical agreements.

Reading a vehicle never changes it. Commanding one does. Withholding the
dictionary was never a real security control — it fails against anyone
determined, and it fails completely against the owner of the truck. The boundary
belongs at the ability to command, not the ability to observe.

## License

Dual license:

- **Software and data** — [Apache-2.0](LICENSE)
- **Documentation** (everything under `docs/`, plus any manual content
  referenced from this repo) — [CC BY 4.0](LICENSE.docs)

The Windrose name, logo and vehicle trademarks remain the property of Windrose.
This is not legal advice — see the license texts for full terms.

## Why open?

Technology leadership is not defined by keeping every document behind a wall,
but by how fast the whole industry can move together. We open what helps the
industry move forward — for the advancement of electric truck technology.
