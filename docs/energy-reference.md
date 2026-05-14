# Energy Reference — Aurora Siger MGAB

> Safety thresholds and decision parameters for the autonomous energy management system.
> All constants defined here are the single source of truth —
> referenced in `constants.py`, `decision.py`, and `forecast.py`.
> Values marked as SIMULATED are order-of-magnitude estimates with declared justification.

---

## Authorization Rule — Operational Stage

```
STAGE =
    CRITICAL   if battery_reserve_kwh ≤ BATTERY_MIN_KWH
    CRITICAL   if is_daytime AND balance_kw < ENERGY_CRITICAL_THRESHOLD_KW
    ALERT      if is_daytime AND balance_kw < ENERGY_ALERT_THRESHOLD_KW
    ALERT      if is_daytime AND forecast crosses ENERGY_ALERT_THRESHOLD_KW
                  within FORECAST_HORIZON_CYCLES
    RECOVERING if previous status was CRITICAL and battery recovered
    OPERATIONAL otherwise
```

CRITICAL triggers on battery depletion regardless of time of day.
Daytime balance thresholds are inactive at night — negative balance overnight is expected
physics: solar = 0, E33 offline 70% of nights (NASA NTRS 19790057281). The battery absorbs
the deficit.

---

## BATTERY_MIN_KWH

**Condition:** `battery_reserve_kwh <= BATTERY_MIN_KWH` → CRITICAL
**Threshold:** `BATTERY_MIN_KWH = 187.2 kWh` (derived: `936.0 kWh × 20%`)

**Components:**
- `BATTERY_CAPACITY_KWH = 312.0 kWh` per unit — arXiv:2410.00066
- `BATTERY_COUNT = 3` — 1 reference unit + 2 additional (SIMULATED; sized for worst-case night)
- `BATTERY_TOTAL_CAPACITY_KWH = 936.0 kWh` — derived
- `BATTERY_MIN_PCT = 20.0%` — SIMULATED

**Source:** arXiv:2410.00066 — reference configuration for a 6-person Mars base:
one 312 kWh battery unit. Additional units added as SIMULATED to satisfy worst-case
nighttime survival with 25% safety margin (standard for life-critical power systems).

**Justification:** Battery drain per cycle uses correct physics: `balance_kw × cycle_hours`
(12.0 h day / 12.6 h night). Worst-case calm night drain: `46 kW × 12.6 h = 579.6 kWh`.
Minimum total capacity to survive with 20% reserve: `579.6 / 0.8 = 724.5 kWh`.
3 units (936 kWh) gives 936 × 0.8 = 748.8 kWh usable — 29% above worst-case drain,
satisfying the 25% safety margin standard for life-critical systems (IEC 61508).
When the threshold is crossed, `shutdown_to_stabilize` immediately deactivates all
non-essential modules — leaving only LSS-01 (14 kW). At 187.2 kWh with 14 kW consumption,
the colony has ~13 hours of emergency power before full depletion.

**Reference:** Hartwick, V. L. et al. *Implications of the Enercon E33 for Mars surface wind power*.
Nature Astronomy, 2023. https://doi.org/10.1038/s41550-023-02022-5
**Reference:** arXiv:2410.00066 — Mars surface power and storage reference configuration.

---

## ENERGY_CRITICAL_THRESHOLD_KW

**Condition:** `is_daytime AND balance_kw < ENERGY_CRITICAL_THRESHOLD_KW` → CRITICAL
**Threshold:** `ENERGY_CRITICAL_THRESHOLD_KW = -15.0 kW` (SIMULATED)

**Justification:** A daytime deficit below -15 kW means generation has collapsed beyond
recoverable tolerance — major dust storm reducing solar to near-zero, or turbine failure
during the only generation window. At this rate, the battery depletes by 180 kWh per
Martian sol (15 kW × 12 h), emptying from full in 3.5 sols.
Inactive at night: nighttime deficit is expected and handled by battery discharge.

**Reference:** Hartwick et al. (2023) — 24–35 kW crew consumption for 6-person mission.
**Reference:** arXiv:2410.00066 — energy balance analysis for Mars surface base.

---

## ENERGY_ALERT_THRESHOLD_KW

**Condition:** `is_daytime AND balance_kw < ENERGY_ALERT_THRESHOLD_KW` → ALERT
**Threshold:** `ENERGY_ALERT_THRESHOLD_KW = -5.0 kW` (SIMULATED)

**Justification:** A small daytime deficit (-5 kW) is an early warning: generation is below
consumption despite the solar window being open. This may indicate dust accumulation, a
partial storm, or turbine degradation. The 10 kW gap between ALERT (-5 kW) and CRITICAL
(-15 kW) provides a monitoring window before automatic shutdown is required.

**Reference:** Hartwick et al. (2023) — energy margin analysis for surface operations.

---

## FORECAST_HORIZON_CYCLES

**Threshold:** `FORECAST_HORIZON_CYCLES = 6 cycles` (SIMULATED — 3 Martian sols)

**Justification:** 6 cycles at 12 h/cycle = 3 Martian sols of look-ahead. The Welford
regression predicts whether `cycle_to_balance` will cross `ENERGY_ALERT_THRESHOLD_KW`
within this window. 3 sols is long enough for the crew to respond but short enough to
remain actionable — a 7-sol forecast would generate false alarms from transient variation.

**Reference:** Forecast implementation: `forecast.py` → `will_cross_threshold_soon`.
**Reference:** Welford, B. P. *Note on a Method for Calculating Corrected Sums of Squares
and Products*. Technometrics, 1962. https://doi.org/10.2307/1266577

---

## FORECAST_MIN_CYCLES

**Threshold:** `FORECAST_MIN_CYCLES = 4 cycles` (SIMULATED)

**Justification:** Welford regression requires at least 2 observations for a slope. 4 cycles
is the minimum for a statistically non-trivial fit — it covers 2 day/night pairs, enough to
distinguish trend from single-cycle noise. Before 4 cycles, `is_regression_reliable()` returns
False and the forecast stage is suppressed.

**Reference:** Welford (1962) — incremental linear regression stability.

---

## Battery Sizing — Nighttime Sufficiency Analysis

The battery must cover the nighttime deficit when both solar (= 0) and wind (typically
offline, NASA NTRS 19790057281) are unavailable. Battery update uses correct physics:
`balance_kw × cycle_hours` — 12.0 h for day cycles, 12.6 h for night cycles.

```
Worst-case calm night drain:
  46 kW × 12.6 h = 579.6 kWh

Minimum total capacity (20% reserve, 25% safety margin):
  579.6 / 0.8 × 1.25 = 905.6 kWh  →  3 × 312 = 936 kWh ✓

Usable capacity:  936 × 0.8 = 748.8 kWh  >  579.6 kWh
Safety margin:    748.8 / 579.6 = 1.29  (29% above worst-case)
After quiet night: 936 − 579.6 = 356.4 kWh  >  187.2 kWh minimum ✓
```

**Reference:** NASA. *Mars Fact Sheet*. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html

---

## Summary Table

| Constant | Value | Type | Source |
|---|---|---|---|
| `BATTERY_CAPACITY_KWH` | 312.0 kWh | Referenced | arXiv:2410.00066 |
| `BATTERY_COUNT` | 3 | SIMULATED | Worst-case night survival + 25% margin |
| `BATTERY_TOTAL_CAPACITY_KWH` | 936.0 kWh | Derived | — |
| `BATTERY_MIN_PCT` | 20% | SIMULATED | Grid storage standard |
| `BATTERY_MIN_KWH` | 187.2 kWh | Derived | — |
| `ENERGY_CRITICAL_THRESHOLD_KW` | −15.0 kW | SIMULATED | Hartwick et al. (2023) |
| `ENERGY_ALERT_THRESHOLD_KW` | −5.0 kW | SIMULATED | Hartwick et al. (2023) |
| `FORECAST_HORIZON_CYCLES` | 6 cycles | SIMULATED | 3 Martian sols |
| `FORECAST_MIN_CYCLES` | 4 cycles | SIMULATED | Welford (1962) |
