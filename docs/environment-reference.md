# Environment Reference — Aurora Siger MGAB

> Physical models and environmental constants for the Martian surface simulation.
> All values are grounded in real mission data and peer-reviewed literature.
> Values marked as SIMULATED are order-of-magnitude estimates with declared justification.

---

## Solar Energy Model

### Formula

```
P_solar = AREA × irradiance × EFFICIENCY × (1 − dust) / 1000 × ARRAY_COUNT
```

| Symbol | Value | Source |
|---|---|---|
| `AREA` | 1,000 m² | arXiv:2410.00066 |
| `EFFICIENCY` | 0.29 | SIMULATED — McMillon-Brown et al. (2020) |
| `ARRAY_COUNT` | 1 | arXiv:2410.00066 |
| `dust` | 0.0 – 1.0 degradation factor | Lorenz et al., PSS (2021) |

**Nominal output (clear day, no dust):** `1000 × 500 × 0.29 / 1000 = 145.0 kW`
**At night:** `irradiance = 0.0` → `P_solar = 0 kW` regardless of sensor state.

---

### MARS_SURFACE_IRRADIANCE_WM2

**Value:** `500.0 W/m²` (SIMULATED)

**Source:** NASA TM-102299, Appelbaum & Flood (1989) — top-of-atmosphere irradiance
`MARS_SOLAR_IRRADIANCE_WM2 = 590.0 W/m²`. Surface value estimated at ~15% atmospheric
absorption (CO₂, dust scattering).

**Justification:** 500 W/m² is conservative for a top-3 wind site (Hartwick 2023), which
correlates with lower dust optical depth and higher solar transmission. Applied as the
baseline for a clear day in the simulation.

**Reference:** Appelbaum, J.; Flood, D. J. *Solar Radiation on Mars*. NASA TM-102299, 1989.
**Reference:** Hartwick, V. L. et al. *Implications of the Enercon E33 for Mars surface wind power*.
Nature Astronomy, 2023. https://doi.org/10.1038/s41550-023-02022-5

---

### SOLAR_PANEL_EFFICIENCY

**Value:** `0.29` (SIMULATED)

**Justification:** State-of-the-art multi-junction cells reach 29–32% under AM0 conditions.
29% is conservative given Martian AM conditions and thermal cycling across the −125 °C to
+20 °C surface range.

**Reference:** McMillon-Brown, L. et al. *High-efficiency photovoltaic cells for space applications*.
ScienceDirect, 2020. https://doi.org/10.1016/j.joule.2020.09.004

---

### SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE

**Value:** `0.002` (0.2% per cycle) — Referenced

**Source:** Lorenz, R. D. et al. *Dust devil activity at the InSight landing site*.
Planetary and Space Science, 2021. InSight lander experienced ~0.1–0.3% solar panel
efficiency loss per sol from dust deposition. 0.2%/cycle (12 h) matches the lower bound —
conservative for a high-latitude site where wind-cleaning events are more frequent.

**Reference:** Lorenz, R. D. et al. *Dust devil and dust accumulation at InSight*.
Planetary and Space Science, 2021. https://doi.org/10.1016/j.pss.2021.105237

---

### SOLAR_DUST_CRITICAL_THRESHOLD

**Condition:** `solar_dust_accumulation >= 0.60` → emergency maintenance
**Threshold:** `SOLAR_DUST_CRITICAL_THRESHOLD = 0.60`

**Source:** InSight lander telemetry — progressive dust accumulation reduced array output
by over 95% before mission end (ScienceDirect, 2024).

**Justification:** At 60% accumulated dust, solar output drops to 40% of nominal
(145 kW → 58 kW), which is below total consumption (46 kW) with no wind margin.
Emergency cleaning is mandatory at this level.

**Reference:** NASA InSight Mission. *Solar panel power degradation*. ScienceDirect, 2024.

---

## Wind Energy Model — Enercon E33

### Formula

```
P_wind = ½ × ρ × A × v³ × η × (1 − abrasion) / 1000 × TURBINE_COUNT
```

| Symbol | Value | Source |
|---|---|---|
| `ρ` | 0.017 kg/m³ | arXiv:2410.00066 |
| `A` | 876.2 m² (π × 16.7²) | Enercon E33 spec |
| `η` | 0.35 | SIMULATED |
| `TURBINE_COUNT` | 2 | arXiv:2410.00066 + redundancy |

---

### Why the E33 generates ~10 kW on Mars vs 330 kW on Earth

```
P ∝ ρ × v³

ρ_Mars / ρ_Earth = 0.017 / 1.225 = 1.4%
```

At identical wind speed, Martian power output is 1.4% of terrestrial rated output.
At top-3 wind sites (Hartwick 2023), diurnal average reaches ~24 kW/turbine.
Planetary average is ~10 kW/turbine. This is confirmed physics — not a modeling error.

**Reference:** Hartwick et al. (2023) — Table 2: E33 diurnal averages by site.
**Reference:** arXiv:2410.00066 — Mars wind power density analysis.

---

### MARS_AIR_DENSITY_KGM3

**Value:** `0.017 kg/m³` — Referenced

**Source:** arXiv:2410.00066. Mars mean surface atmospheric density — approximately 1.4% of
Earth sea-level density (1.225 kg/m³). Varies with altitude, season, and dust loading;
0.017 kg/m³ is the reference surface value used for the E33 performance calculation.

**Reference:** arXiv:2410.00066. https://arxiv.org/abs/2410.00066

---

### WIND_CUT_IN_MS / WIND_CUT_OUT_MS

**Values:** `10.3 m/s` (cut-in) · `115.7 m/s` (cut-out) — Referenced

**Source:** arXiv:2410.00066 — E33 operating envelope recalculated for Martian atmosphere.
Cut-in speed is much higher than Earth (3 m/s) because lower air density requires higher
velocity to reach the minimum aerodynamic torque needed to spin the rotor.

**Reference:** arXiv:2410.00066. Mars-adapted E33 performance curve.

---

### WIND_TURBINE_EFFICIENCY

**Value:** `0.35` (SIMULATED)

**Justification:** The Betz limit is 16/27 ≈ 0.593. Modern turbines reach 45–50% of Betz
in terrestrial conditions. 0.35 (59% of Betz) is conservative for Martian conditions where
blade tip Reynolds number is significantly lower, reducing aerodynamic efficiency.
arXiv:2410.00066 uses a full Cp curve; 0.35 approximates the mean operating point.

**Reference:** Betz, A. *Wind-Energie und ihre Ausnutzung durch Windmühlen*. 1926.
**Reference:** arXiv:2410.00066 — Cp curve for Mars-adapted E33.

---

### Colony Location — Top-3 Wind Sites

**Value:** `COLONY_LOCATION = "Top-3 wind sites, Hartwick et al. (2023)"`

**Justification:** The 24 kW/turbine diurnal average is valid only for the top-3 sites
identified by Hartwick et al. (2023). Site selection by wind energy resource is the
methodology recommended by the paper. Using the planetary average (10 kW) would require
more turbines to meet the 46 kW consumption floor.

**Reference:** Hartwick, V. L. et al. *Implications of the Enercon E33 for Mars surface
wind power*. Nature Astronomy, 2023. https://doi.org/10.1038/s41550-023-02022-5

---

## Day/Night Cycle

**Values:** `MARTIAN_DAY_HOURS = 12.0 h` · `MARTIAN_NIGHT_HOURS = 12.6 h`

**Source:** NASA Mars Fact Sheet — Martian sol = 24.6 h. Simulation uses 12 h / 12.6 h
split (approximate equinox conditions). Battery delta per cycle:
`balance_kw × 12 h` (day) or `balance_kw × 12.6 h` (night).

**Reference:** NASA. *Mars Fact Sheet*. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html

---

## Nighttime Wind Statistics

**Value:** `NIGHT_QUIET_PROBABILITY = 0.70` — Referenced

**Source:** NASA NTRS 19790057281 — Viking Lander 2 meteorological data.
Nighttime conditions were "usually very quiet" across all seasons — 70% of nights recorded
wind speeds below the E33 cut-in threshold (10.3 m/s). This means the turbine is offline
70% of nights, making the battery the sole energy source during those periods.

**Reference:** NASA NTRS 19790057281. *Viking Lander Meteorology Data Analysis*. 1979.
https://ntrs.nasa.gov/citations/19790057281

---

## Dust Storm Model

### Duration

**Values:** `DUST_STORM_MIN_DURATION_CYCLES = 6` · `DUST_STORM_MAX_DURATION_CYCLES = 56`

| Bound | Cycles | Martian sols | Source |
|---|---|---|---|
| Minimum | 6 | 3 sols | ScienceDirect (2022) — regional storm minimum |
| Maximum | 56 | ~4 weeks | ScienceDirect (2022) — regional storm maximum |

MGAB models regional storms only. Global storms (weeks to months) are out of scope.

**Reference:** ScienceDirect (2022) — Mars dust storm climatology and duration statistics.

---

### Storm Solar Reduction

**Value:** `STORM_SOLAR_RESIDUAL_FACTOR = 0.05` (SIMULATED)

```
P_solar_storm = irradiance × (1 − intensity × 0.85)
```

At peak intensity (1.0): solar reduced to 15% of nominal, consistent with InSight telemetry
where panels lost over 95% output during the 2022 regional storm (ScienceDirect, 2024).
The 0.05 floor prevents absolute zero — diffuse sky light persists even in severe storms.

**Reference:** NASA InSight Mission. *Solar panel power loss during 2022 dust storm*. ScienceDirect, 2024.

---

### Storm Wind Behavior

**Daytime during storm:** wind elevated to `[17, 21] m/s` — above E33 cut-in
**Nighttime during storm:** `STORM_NIGHT_QUIET_PROBABILITY = 0.60` calm nights (reduced from nominal 0.70)

**Source:** Daytime storm winds derived from Perez-Prada et al. (2021) — storm-season
threshold 17 m/s (Viking Lander 2). Nighttime: NASA NTRS 19790057281 — storm conditions
increase low-level turbulence but still produce calm episodes.

**Reference:** Perez-Prada, A. et al. *Martian dust storm season wind statistics*.
ScienceDirect, 2021.
**Reference:** NASA NTRS 19790057281. *Viking Lander Meteorology*, 1979.

---

## Temperature

| Constant | Value | Source |
|---|---|---|
| `MARS_EXTERNAL_TEMP_MIN_C` | −125 °C | NASA Mars Fact Sheet |
| `MARS_EXTERNAL_TEMP_MAX_C` | +20 °C | NASA Mars Fact Sheet |
| `COLONY_INTERNAL_TEMP_NOMINAL_C` | 21 °C | SIMULATED — human thermal comfort |

**Reference:** NASA. *Mars Fact Sheet*. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html

---

## Wind Speed Range

| Constant | Value | Source |
|---|---|---|
| `MARS_WIND_SPEED_MIN_MS` | 2.0 m/s | NASA PDS Viking Meteorology Data — calm conditions |
| `MARS_WIND_SPEED_MAX_MS` | 30.0 m/s | NASA PDS Viking Meteorology Data — peak storm winds |
| `MARS_WIND_STORM_MIN_MS` | 17.0 m/s | Perez-Prada et al., ScienceDirect (2021) |
| `MARS_WIND_NIGHT_TYPICAL_MS` | 5.0 m/s | NASA NTRS 19790057281 — "nighttime usually very quiet" |

**Reference:** NASA PDS. *Viking Meteorology Instrument System Data*. VL1/VL2-M-MET-4-BINNED-P-T-V-V1.0.

---

## Summary Table

| Constant | Value | Type | Source |
|---|---|---|---|
| `MARS_SURFACE_IRRADIANCE_WM2` | 500 W/m² | SIMULATED | NASA TM-102299 + 15% atm. loss |
| `SOLAR_PANEL_AREA_M2` | 1,000 m² | Referenced | arXiv:2410.00066 |
| `SOLAR_PANEL_EFFICIENCY` | 0.29 | SIMULATED | McMillon-Brown et al. (2020) |
| `MARS_AIR_DENSITY_KGM3` | 0.017 kg/m³ | Referenced | arXiv:2410.00066 |
| `WIND_TURBINE_DIAMETER_M` | 33.4 m | Referenced | Enercon E33 spec |
| `WIND_CUT_IN_MS` | 10.3 m/s | Referenced | arXiv:2410.00066 |
| `WIND_CUT_OUT_MS` | 115.7 m/s | Referenced | arXiv:2410.00066 |
| `WIND_AVERAGE_POWER_KW_BEST_SITES` | 24 kW/turbine | Referenced | Hartwick et al. (2023) |
| `NIGHT_QUIET_PROBABILITY` | 0.70 | Referenced | NASA NTRS 19790057281 |
| `DUST_STORM_MIN_DURATION_CYCLES` | 6 cycles | Referenced | ScienceDirect (2022) |
| `DUST_STORM_MAX_DURATION_CYCLES` | 56 cycles | Referenced | ScienceDirect (2022) |
