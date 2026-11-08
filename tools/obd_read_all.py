#!/usr/bin/env python3
"""Read as much as possible from a Windrose E700 through the 16-pin OBD port.

Read only. It sends nothing but questions:
  UDS  $3E 00 (who is there), $10 01 / $10 03, $22 identification DIDs,
       $19 01 / $19 02 (fault codes), and ISO-TP flow control
  J1939 Request (PGN 59904) for DM1, DM2, DM5, DM6, DM12, VI, CI, SOFT
Everything else is refused before it reaches the bus (see is_allowed()).

Every frame seen or sent goes into an .asc log. A plain-text summary is written
next to it. Send both to Windrose.

  pip install python-can
  python obd_read_all.py                       # PEAK, classic CAN 500 kbit/s
  python obd_read_all.py --fd                  # CAN FD 500k / 2M
  python obd_read_all.py --interface kvaser --channel 0

Ignition ON. Close PCAN-View and other CAN programs first. See docs/obd.md.
"""
import argparse
import datetime as dt
import os
import sys
import time

import can

TESTER = 0xF1
FUNCTIONAL = 0x18DBFFF1
J1939_SA = 0xF9  # off-board diagnostic tool

KNOWN_ECUS = {
    0xFB: "Gateway", 0x27: "VDC powertrain", 0x21: "BDCU body", 0x41: "CDCU cabin",
    0x17: "Instrument cluster", 0x74: "Inverter 1", 0x75: "Inverter 2",
    0x76: "Inverter 3", 0x77: "Inverter 4", 0x03: "Transmission",
    0xA6: "Battery domain", 0x78: "HV distribution", 0x0B: "EBS brakes",
    0x50: "EPB park brake", 0x2F: "ECAS air suspension", 0x13: "Steering assist",
    0x54: "Junction box upper", 0x59: "Junction box under", 0x19: "HVAC",
    0x33: "TPMS", 0x6F: "DC/DC 1", 0x70: "DC/DC 2",
}

DIDS = {
    0xF190: "VIN", 0xF187: "Spare part number", 0xF18C: "Serial number",
    0xF193: "Hardware version", 0xF195: "Software version",
    0xF1A1: "Vehicle configuration", 0xF010: "CDCU option bitmap",
}

J1939_ASKS = {
    65226: "DM1 active faults", 65227: "DM2 previous faults", 65230: "DM5 readiness",
    65231: "DM6 pending faults", 65236: "DM12 emission faults",
    65260: "VI vehicle id", 65259: "CI component id", 65242: "SOFT software id",
}
J1939_FORBIDDEN = {65228, 65235}  # DM3, DM11 clear faults

NRC = {0x11: "service not supported", 0x12: "sub-function not supported",
       0x13: "wrong length", 0x22: "conditions not correct",
       0x31: "request out of range", 0x33: "security access denied",
       0x7E: "not supported in this session", 0x7F: "service not supported in this session"}


def is_allowed(arb_id, data):
    """Last gate before the bus. Questions only."""
    if (arb_id & 0xFFFF00FF) == 0x18DA00F1 or arb_id == FUNCTIONAL:
        pci = data[0] >> 4
        if pci == 0x3:                      # ISO-TP flow control
            return True
        if pci != 0x0:                      # we only ever send single frames
            return False
        n = data[0] & 0x0F
        sid = data[1:1 + n]
        if not sid:
            return False
        if sid[0] == 0x3E:
            return list(sid) == [0x3E, 0x00]
        if sid[0] == 0x10:
            return len(sid) == 2 and sid[1] in (0x01, 0x03)
        if sid[0] == 0x22:
            return len(sid) == 3
        if sid[0] == 0x19:
            return len(sid) >= 2 and sid[1] in (0x01, 0x02, 0x0A)
        return False
    if (arb_id & 0x00FFFF00) == 0x00EAFF00 and (arb_id & 0xFF) == J1939_SA:
        pgn = data[0] | (data[1] << 8) | (data[2] << 16)
        return pgn in J1939_ASKS and pgn not in J1939_FORBIDDEN
    return False


class Reader:
    def __init__(self, bus, log):
        self.bus, self.log = bus, log
        self.seen = {}

    def send(self, arb_id, data):
        data = bytes(data) + bytes([0xAA] * (8 - len(data)))
        if not is_allowed(arb_id, data):
            raise SystemExit("refused to send %08X %s" % (arb_id, data.hex()))
        msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id=True,
                          is_rx=False, timestamp=time.time())
        self.bus.send(msg)
        self.log.on_message_received(msg)

    def recv(self, timeout):
        msg = self.bus.recv(timeout)
        if msg is not None:
            self.log.on_message_received(msg)
            self.seen[msg.arbitration_id] = self.seen.get(msg.arbitration_id, 0) + 1
        return msg

    def listen(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.recv(0.1)

    def who_is_there(self):
        self.send(FUNCTIONAL, [0x02, 0x3E, 0x00])
        found, end = set(), time.time() + 1.0
        while time.time() < end:
            m = self.recv(0.05)
            if m and (m.arbitration_id & 0xFFFF0000) == 0x18DA0000 \
                    and ((m.arbitration_id >> 8) & 0xFF) == TESTER and m.data[1:2] == b"\x7E":
                found.add(m.arbitration_id & 0xFF)
        return found

    def ask(self, ecu, payload, timeout=1.0):
        """One UDS request, ISO-TP single-frame out, any-length answer back."""
        req, rsp = 0x18DA00F1 | (ecu << 8), 0x18DAF100 | ecu
        self.send(req, [len(payload)] + list(payload))
        buf, need, sn = b"", None, 1
        end = time.time() + timeout
        while time.time() < end:
            m = self.recv(0.05)
            if not m or m.arbitration_id != rsp:
                continue
            pci = m.data[0] >> 4
            if pci == 0:
                body = bytes(m.data[1:1 + (m.data[0] & 0x0F)])
                if body[:1] == b"\x7F" and body[2:3] == b"\x78":   # response pending
                    end = time.time() + 5.0
                    continue
                return body
            if pci == 1:
                need = ((m.data[0] & 0x0F) << 8) | m.data[1]
                buf = bytes(m.data[2:])
                self.send(req, [0x30, 0x00, 0x00])
                end = time.time() + timeout
            elif pci == 2 and need is not None:
                if (m.data[0] & 0x0F) != sn % 16:
                    return None
                sn += 1
                buf += bytes(m.data[1:])
                if len(buf) >= need:
                    return buf[:need]
        return None

    def j1939(self, pgn):
        self.send(0x18EAFF00 | J1939_SA, [pgn & 0xFF, (pgn >> 8) & 0xFF, (pgn >> 16) & 0xFF])
        self.listen(1.5)


def show(body):
    if body is None:
        return "no answer"
    if body[:1] == b"\x7F":
        code = body[2] if len(body) > 2 else 0
        return "refused: 0x%02X %s" % (code, NRC.get(code, ""))
    return body.hex(" ")


def ascii_or_hex(b):
    t = b.decode("ascii", "replace").strip("\x00 ")
    return t if t and all(32 <= ord(c) < 127 for c in t) else b.hex(" ")


def dtcs(body):
    """$19 02 answer: 59 02 <mask> then 4 bytes per code."""
    out = []
    for i in range(3, len(body) - 3, 4):
        code, status = body[i:i + 3], body[i + 3]
        out.append("%s status 0x%02X" % (code.hex().upper(), status))
    return out


def open_bus(a):
    kw = dict(interface=a.interface, channel=a.channel)
    if a.fd:
        kw.update(fd=True, f_clock_mhz=80, nom_brp=2, nom_tseg1=63, nom_tseg2=16, nom_sjw=16,
                  data_brp=2, data_tseg1=15, data_tseg2=4, data_sjw=4)
    else:
        kw.update(bitrate=a.bitrate)
    return can.Bus(**kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--interface", default="pcan")
    ap.add_argument("--channel", default="PCAN_USBBUS1")
    ap.add_argument("--bitrate", type=int, default=500000)
    ap.add_argument("--fd", action="store_true", help="CAN FD, 500 kbit/s + 2 Mbit/s")
    ap.add_argument("--listen", type=float, default=10.0, help="seconds of listening first")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(a.out, "obd-read-" + stamp)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    bus = open_bus(a)
    log = can.ASCWriter(base + ".asc")
    r = Reader(bus, log)
    try:
        say("Windrose OBD read-all  %s  %s %s" % (stamp, a.interface,
            "CAN FD 500k/2M" if a.fd else "classic %d" % a.bitrate))
        say("1. Listening %.0f s (nothing sent)" % a.listen)
        r.listen(a.listen)
        say("   %d CAN IDs, %d frames" % (len(r.seen), sum(r.seen.values())))

        say("2. Who is there ($3E functional)")
        found = r.who_is_there()
        if not found:
            say("   nobody answered; asking the known addresses one by one")
        else:
            say("   answered: " + ", ".join("%02X %s" % (e, KNOWN_ECUS.get(e, "")) for e in sorted(found)))
        ecus = sorted(found | set(KNOWN_ECUS))

        say("3. Identification and fault codes per ECU")
        for ecu in ecus:
            name = KNOWN_ECUS.get(ecu, "unknown")
            first = r.ask(ecu, [0x22, 0xF1, 0x90], timeout=0.5)
            if first is None and ecu not in found:
                continue
            say("-- %02X %s" % (ecu, name))
            for did, label in DIDS.items():
                body = first if did == 0xF190 else r.ask(ecu, [0x22, did >> 8, did & 0xFF])
                if body and body[:1] == b"\x62":
                    say("   %-20s %s" % (label, ascii_or_hex(body[3:])))
                elif body is not None and body[:1] == b"\x7F" and body[2:3] == b"\x31":
                    continue
                else:
                    say("   %-20s %s" % (label, show(body)))
            body = r.ask(ecu, [0x19, 0x02, 0xFF], timeout=2.0)
            if body and body[:2] == b"\x59\x02":
                codes = dtcs(body)
                say("   fault codes: %d" % len(codes))
                for c in codes:
                    say("     " + c)
            else:
                say("   fault codes: " + show(body))

        say("4. J1939 requests")
        for pgn, label in J1939_ASKS.items():
            before = sum(r.seen.values())
            r.j1939(pgn)
            say("   %-22s %d frames after the request" % (label, sum(r.seen.values()) - before))

        say("5. Listening 5 s more")
        r.listen(5)
        say("Done. %d CAN IDs, %d frames in total." % (len(r.seen), sum(r.seen.values())))
    finally:
        log.stop()
        bus.shutdown()
        with open(base + ".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("\nSaved %s.asc and %s.txt. Send both to Windrose." % (base, base))


if __name__ == "__main__":
    sys.exit(main())
