# Field faults seen on E700 trucks

Faults reported from trucks in service in Europe, the Americas, Australia and
China, 2026. Each entry gives what was reported, what was done, and what is
still unknown. No customer names, VINs or prices are given. "Root cause not
established" means exactly that: the part was changed and the fault went away,
or the case is still open.

Look fault codes up in [`dtc/windrose_dtc_public.csv`](../dtc/). For how to
read them, see [`docs/obd.md`](obd.md).

## Reading the truck

### Listen-only OBD recordings come back empty or full of errors

- **Seen:** a dealer recorded a stopped truck through the OBD port and the file
  came back empty. On another truck, a PEAK adapter at classic CAN 500 kbit/s
  sat at its bus-error warning limit: in 10 s it logged about 10,000 frames
  under 2 IDs, which were error frames, and no ECU answered.
- **Why it matters:** the OBD port is a diagnostic port behind the gateway.
  Little traffic is forwarded unprompted, and a controller at the wrong bit
  rate (for example classic CAN on a CAN FD segment) sees only errors.
- **What to do:** use [`tools/obd_read_all.py`](../tools/obd_read_all.py). It
  finds the bus setting listen-only before it asks anything, and stops without
  sending if every setting gives errors.
- **Still open:** whether the OBD diagnostic CAN on pins 6/14 runs classic CAN
  or CAN FD frames.

## Electrical

### Trailer turn and brake lights out, rest of the lights fine

- **Seen:** trailer turn signals and brake lights stopped working; every other
  lamp on the truck worked. The truck could not continue with the trailer.
- **Done:** resetting the starter battery restored the lights. Afterwards the
  fog light could not be switched on.
- **Background:** there is no conventional fuse box. Lamps are fed by two smart
  junction boxes. On the chassis box, outputs OUT14 / OUT15 feed the left /
  right brake lamps, OUT31 the EBS trailer supply and OUT13 the marker lamps.
  The trailer turn signals come from the body controller (BDCU); its codes
  `B150130` / `B150330` mean trailer turn lamp open circuit and `B150034` /
  `B150234` short to ground (service manual 7.9.5.10 and 7.9.5.11). A junction
  box output that trips on overcurrent or short recovers after a KL15 cycle or
  a restart.
- **Root cause:** not established. The wiring from the trailer socket to the
  brake-lamp outputs is not in the manual.

### Chassis smart junction box with copper corrosion

- **Seen:** a truck had its chassis smart junction box (SJB-DOWN) replaced in
  the field. The removed unit showed copper corrosion.
- **Status:** the unit went back for failure analysis. Result not yet known.

### 12 V auxiliary batteries

- The truck carries **two 12 V, 60 Ah lead-acid batteries** in series for the
  24 V system.
- When a local replacement is needed, match capacity (about 60 Ah) and check
  the case size, terminal side and hold-down against the original before
  buying. North American BCI group 48 (H6) cases are 278 × 175 × 190 mm and
  group 96R cases 242 × 173 × 175 mm; the original's case size is not given
  here.

### Truck shows SOC 0 % at ignition on and will not start

- **Seen (open case):** at IG-on the cluster shows SOC 0 %, air pressure
  0.0 / 6.9 psi, several red and amber warnings, gear N. The truck does not
  get ready to drive.
- **Status:** open. Fault codes are being read through the OBD port.

### Cluster shows fault codes frequently

- **Seen:** a truck in China showed fault codes on the cluster again and again.
  Codes and outcome were not recorded in a way that can be published.

## Powertrain

### Loss of regenerative braking and power, four-motor truck

- **Seen:** a four-motor LFP truck working in a mining area lost regenerative
  braking and then drive power. It stood for more than five weeks.
- **Done:** e-axle motor and inverter parts were shipped and fitted. An earlier
  attempt to read the truck produced an empty file (see above).
- **Root cause:** not established.

### Inverter reports internal temperature sensor fault

- **Seen:** one e-axle's inverter (MCU) reported an internal temperature sensor
  fault.
- **Status:** whether the whole e-axle assembly must be replaced was still
  being decided.

### Transmission self-check not passed

- **Seen:** `TCU_Selfcheck_status = self-check not passed` on a two-speed e-axle
  gearbox.
- **What it takes:** a TCU self-learn started from the powertrain controller.
  That needs a Windrose service session; it cannot be done with read-only
  tools.

### E-axle oil leak

- **Seen:** oil leaking from an e-axle on a truck in Australia.
- **Status:** reported; the fix was not recorded.

### Battery pack does not charge to full

- **Seen:** a truck in China did not charge its pack to full.
- **Status:** open.

## Brakes and chassis

### Park brake will not hold, or releases by itself

- **Seen on several trucks (China and USA):** pulling the park brake switch
  does not apply the park brake; on one truck it applied, then released
  automatically within 3 s of letting go of the service brake pedal. On a US
  truck the park brake could not be applied or released and the code was
  `14418 11` (EPB connection signal fault).
- **Done:** in every case the park brake switch was replaced, and where
  checked the fault went away.
- **Root cause:** not established. If you see it, record the codes from the
  EPB module before changing the switch.

### EBS steering-angle calibration and ESC initialisation

- After work on steering or the EBS, the steering-angle sensor must be
  calibrated and the ESC initialised with the brake supplier's diagnostic
  software. Two trucks in Australia needed this.

### Threaded fixing points strip on re-assembly

- **Seen:** several weld nuts and rivet nuts on the body and brackets lost their
  thread after being assembled once and taken apart again.
- **Status:** reported to the body supplier.

### Chassis rust on an early truck

- **Seen:** rust on the chassis of the first truck delivered to Australia; it
  went to a body shop for repair and paint.

### Tyres worn at 12,000 km

- **Seen:** a Norwegian truck needed new tyres at about 12,000 km against an
  expected 100,000 km. The operator asked for a torque reduction to be
  programmed.
- **Status:** open.

## Air system

### Seat air line leaking at an inline one-way valve

- **Seen (US truck):** with the tank at 40 psi and filling, air leaked at both
  connections of an inline one-way valve in the driver's seat air line. Holding
  the hose stopped the leak. The seat rose, dropped slightly and then held.
- **Done:** a technician removed the valve and the leak stopped.
- **Unknown:** what the valve is for in the seat system, and whether the seat
  works fully without it.

### Compressor noise

- **Seen:** air compressor noise reported in Norway; "compressor noise" also
  reported in Israel, without saying whether air or A/C compressor.
- **Status:** open.

### Air pressure sensors moved between trucks

- Two air pressure sensors were moved from one US truck to another to get it
  ready for a customer trial. Not a fault in itself; noted because the donor
  truck was then without them.

## Cab and body

### HVAC front-left mode flap

- **Seen (two trucks):** the air-conditioning controller reported `B250117`,
  front-left mode flap motor 1 actuator fault: the face / defrost mode actuator,
  its three wires and connector, or the flap it drives.
- **Status:** open.

### Charging flap will not open, or charging port will not close

- **Seen (China):** on one truck the charging flap would not open; on another
  the left charging port would not close.

### Camera mirror arm broken

- **Seen (UK):** the right camera mirror arm was broken. Mechanical damage, not
  a fault code.

### Side marker lamp and bracket damaged in transport

- **Seen (Norway):** side marker lamp and its black cover damaged on delivery.

## Service information that dealers asked for

- **"Where is this part fitted?"** Service stations could not tell where some
  parts sit from the parts catalogue. The exploded views of the after-sales
  catalogue answer this.
- **OBD pinout.** See [`docs/obd.md`](obd.md).
- **Fuses.** There is no conventional fuse box; see the trailer-lights entry
  above.

## Add a case

Open an issue with: what the truck did, the fault codes (with the ECU and the
code type), what was changed, and whether that fixed it. Leave out VINs and
customer names.
