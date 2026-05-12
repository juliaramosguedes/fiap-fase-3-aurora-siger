# Modules Reference — Aurora Siger MGAB

> Consumption, priority, and operational rationale for the 8 colony modules.
> All consumption values are SIMULATED — proportional distribution anchored to
> Hartwick et al. (2023): 24–35 kW for a 6-person, 500-sol Mars mission.
> All modules operate 24h: shutdown is energy-driven, not schedule-driven.

---

## 24h Operation Rationale

All 8 modules operate continuously. There is no day/night module schedule.

**Sources:**
- CELSS (NIH, 2019): "life support systems were controlled automatically" — continuous operation implied
- NASA ECLSS (NTRS 20230002103): "automation to reduce regular maintenance time" — 24h automated ops
- Space S&T (2021): ISRU "can operate 24h or 8h — decision of energy, not of people"

The nighttime energy deficit is physical, not operational: solar = 0, E33 offline 70% of nights
(NASA NTRS 19790057281). The battery absorbs the deficit. When it depletes, the system enters
CRITICAL and shuts down the lowest-priority module — not a pre-scheduled module.

**Reference:** NIH. *Controlled Ecological Life Support Systems (CELSS)*. 2019.
**Reference:** NASA ECLSS. NTRS 20230002103. *Environmental Control and Life Support System Overview*.
**Reference:** NASA NTRS 19790057281. *Viking Lander Meteorology*, 1979.

---

## Total Consumption Anchor

```
Total nominal consumption = 46 kW (all 8 modules active)
```

**Source anchor:** Hartwick et al. (2023) — 24–35 kW for crew life support + habitation,
6-person mission. Simulation adds 16 kW for operational infrastructure modules
(COM-01, SCI-01, LOG-01, MIN-01 at 3–5 kW each). Total: ~30 kW + 16 kW = 46 kW.

**Reference:** Hartwick, V. L. et al. *Implications of the Enercon E33 for Mars surface
wind power*. Nature Astronomy, 2023. https://doi.org/10.1038/s41550-023-02022-5

---

## Module Definitions

### LSS-01 — Life Support System

| Attribute | Value | Source |
|---|---|---|
| Priority | 1 (never shut down) | NASA HRP — life support is prerequisite for crew survival |
| Consumption | 14.0 kW | SIMULATED |
| Function | Air revitalization, pressure, water recycling, thermal control |

**Justification:** NASA ECLSS on ISS consumes approximately 13.5 kW for a 6-person crew
(NTRS 20230002103). 14 kW accounts for ECLSS equivalent plus redundant thermal control in
Martian conditions (−125 °C external, 21 °C internal — delta of 146 °C).

**Shutdown rule:** Priority = 1. LSS-01 is excluded from automatic shutdown by
`shutdown_lowest_priority_module`, which filters `priority > 1`.

**Reference:** NASA ECLSS. NTRS 20230002103. *Environmental Control and Life Support
System Overview*. 2023.
**Reference:** NASA Human Research Program. *Life Support Systems*.
https://www.nasa.gov/hrp

---

### MED-01 — Medical Support

| Attribute | Value | Source |
|---|---|---|
| Priority | 2 | NASA HRP — medical emergencies have a critical time window |
| Consumption | 5.0 kW | SIMULATED |
| Function | Medical monitoring, surgical suite, pharmaceutical storage |

**Justification:** NASA's Human Research Program identifies 5 hazards for long-duration
spaceflight — isolation/confinement, distance from Earth, hostile environment, space weather,
and gravity fields — all present on Mars. Medical infrastructure cannot be deferred.
5 kW covers powered surgical instruments, refrigerated pharmaceuticals, and continuous
vital monitoring.

**Reference:** NASA Human Research Program. *Human Research Roadmap — The 5 Hazards*.
https://humanresearchroadmap.nasa.gov/

---

### HAB-01 — Habitat

| Attribute | Value | Source |
|---|---|---|
| Priority | 3 | Crew shelter required before any secondary operations |
| Consumption | 7.0 kW | SIMULATED |
| Function | HVAC, lighting, pressurization, structural monitoring |

**Justification:** 7 kW covers habitat pressurization pumps (~2 kW), HVAC fans and heaters
(~3 kW, given 146 °C internal-external delta), LED lighting (~1 kW), and structural
sensors (~1 kW). Based on NASA Lunar Gateway habitat power budgets scaled for Mars
thermal load.

**Reference:** Hartwick et al. (2023) — habitation power included in crew consumption estimate.
**Reference:** NASA. *Gateway Habitation and Logistics Outpost (HALO)*. 2021.

---

### PWR-01 — Power Systems

| Attribute | Value | Source |
|---|---|---|
| Priority | 4 | Power distribution must remain active to route generation to consumers |
| Consumption | 4.0 kW | SIMULATED |
| Function | Power distribution, inverters, DC-AC conversion, battery management |

**Justification:** Power electronics (inverters, charge controllers, DC bus management)
consume 2–5% of total system capacity as conversion losses. At 46 kW total consumption,
4 kW (8.7%) covers power conditioning plus battery management systems for two 312 kWh units.

**Reference:** arXiv:2410.00066 — power system architecture for Mars surface base.

---

### COM-01 — Communications

| Attribute | Value | Source |
|---|---|---|
| Priority | 5 | Operational comms — non-critical for immediate survival |
| Consumption | 3.0 kW | SIMULATED |
| Function | Antennas, transponders, Earth-Mars relay, inter-module network |

**Justification:** NASA Deep Space Network link budgets for Mars surface operations require
1–3 kW for UHF/X-band transponders during communication windows. 3 kW covers continuous
relay operation plus local surface network infrastructure.

**Reference:** NASA JPL. *Deep Space Network Telecommunications Link Design Handbook*. 2010.

---

### SCI-01 — Science Laboratory

| Attribute | Value | Source |
|---|---|---|
| Priority | 6 | Research begins only after colony is stabilized |
| Consumption | 5.0 kW | SIMULATED |
| Function | Surface analysis instruments, sample processing, data storage |

**Justification:** Zubrin (1996) establishes that science operations begin after survival
infrastructure is active. 5 kW covers analytical instruments (mass spectrometer,
X-ray diffractometer), environmental monitoring stations, and data storage/transmission.

**Reference:** Zubrin, R.; Wagner, R. *The Case for Mars*. Simon & Schuster, 1996.

---

### LOG-01 — Logistics

| Attribute | Value | Source |
|---|---|---|
| Priority | 7 | Colony sustenance — lower priority than science infrastructure |
| Consumption | 3.0 kW | SIMULATED |
| Function | Rover charging, EVA suit maintenance, pressurized storage |

**Justification:** Logistics operations are intermittent. 3 kW represents trickle charging
for surface rovers (~1 kW each × 2) plus EVA suit recharging and pressurized cargo bay
thermal management.

**Reference:** SpaceX. *Starship cargo configuration for Mars*. https://www.spacex.com/vehicles/starship/

---

### MIN-01 — ISRU Mining

| Attribute | Value | Source |
|---|---|---|
| Priority | 8 (first to shut down) | Long-term capability — not immediate survival |
| Consumption | 5.0 kW | SIMULATED |
| Function | In-situ resource utilization: O₂ and H₂O extraction, regolith processing |

**Justification:** NASA MOXIE demonstrated O₂ production at ~300 W on Perseverance (2021).
Full-scale ISRU for a 6-person base requires roughly 2–10 kW depending on production rate.
5 kW covers basic O₂ and H₂O extraction without methane propellant production (out of scope).
MIN-01 is first to shut down in CRITICAL because ISRU output can be interrupted without
immediate crew risk — stored O₂ and H₂O buffers provide short-term margin.

**Reference:** NASA. *MOXIE*. Perseverance Rover, 2021.
https://mars.nasa.gov/mars2020/spacecraft/instruments/moxie/
**Reference:** NASA. *In-Situ Resource Utilization*. NASA ISRU Roadmap, 2023.
https://www.nasa.gov/isru

---

## Priority Rationale Summary

The priority order follows the **survival-first principle** established by NASA HRP
and the Mars Direct architecture (Zubrin, 1996):

1. **Life support first** — without LSS-01 the crew cannot survive; it is never shut down
2. **Medical second** — crew health takes precedence over mission productivity
3. **Habitat third** — pressurized shelter is prerequisite for all surface operations
4. **Power fourth** — power distribution must stay active to route generation
5. **Communications fifth** — critical for safety, but crew can survive brief outages
6. **Science sixth** — mission productivity, not survival
7. **Logistics seventh** — intermittent operations with short-term buffer tolerance
8. **ISRU last** — long-term colony capability; stored reserves bridge any shutdown gap

**Reference:** NASA Human Research Program. *Human Research Roadmap*.
https://humanresearchroadmap.nasa.gov/
**Reference:** Zubrin, R.; Wagner, R. *The Case for Mars*. Simon & Schuster, 1996.

---

## Summary Table

| Module | Consumption | Priority | Type | Shutdown Eligible |
|---|---|---|---|---|
| LSS-01 Life Support | 14.0 kW | 1 | SIMULATED | No — `priority > 1` filter |
| MED-01 Medical | 5.0 kW | 2 | SIMULATED | Yes |
| HAB-01 Habitat | 7.0 kW | 3 | SIMULATED | Yes |
| PWR-01 Power Systems | 4.0 kW | 4 | SIMULATED | Yes |
| COM-01 Communications | 3.0 kW | 5 | SIMULATED | Yes |
| SCI-01 Science Lab | 5.0 kW | 6 | SIMULATED | Yes |
| LOG-01 Logistics | 3.0 kW | 7 | SIMULATED | Yes |
| MIN-01 ISRU Mining | 5.0 kW | 8 | SIMULATED | Yes — first to shut down |
| **Total** | **46.0 kW** | — | — | — |
