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
**Threshold:** `BATTERY_MIN_KWH = 124.8 kWh` (derived: `624.0 kWh × 20%`)

**Components:**
- `BATTERY_CAPACITY_KWH = 312.0 kWh` per unit — arXiv:2410.00066
- `BATTERY_COUNT = 2` — 1 reference unit + 1 redundant (SIMULATED; single-failure tolerance)
- `BATTERY_TOTAL_CAPACITY_KWH = 624.0 kWh` — derived
- `BATTERY_MIN_PCT = 20.0%` — SIMULATED

**Source:** arXiv:2410.00066 — reference configuration for a 6-person Mars base:
one 312 kWh battery unit. Second unit added as SIMULATED redundancy per
single-failure-tolerance design principle (NASA-STD-8729.1).

**Justification:** 20% minimum prevents deep discharge degradation of lithium-ion cells
(standard practice in terrestrial grid storage). At 124.8 kWh with 46 kW total consumption,
the colony has ~2.7 hours of emergency power after the threshold is crossed — sufficient
for a single reactivation cycle before cascade shutdown.

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
offline, NASA NTRS 19790057281) are unavailable.

```
Minimum battery to survive one full night:
  consumption = 46 kW × 12.6 h = 579.6 kWh

Total capacity = 624.0 kWh  →  margin = 44.4 kWh (7.1%)
```

The colony can survive exactly one quiet night at full consumption before depletion.
This tight margin is why `BATTERY_MIN_PCT = 20%` triggers shutdown before the battery
is fully exhausted — to preserve the recovery window.

**Reference:** NASA. *Mars Fact Sheet*. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html

---

## Summary Table

| Constant | Value | Type | Source |
|---|---|---|---|
| `BATTERY_CAPACITY_KWH` | 312.0 kWh | Referenced | arXiv:2410.00066 |
| `BATTERY_COUNT` | 2 | SIMULATED | arXiv:2410.00066 + redundancy |
| `BATTERY_TOTAL_CAPACITY_KWH` | 624.0 kWh | Derived | — |
| `BATTERY_MIN_PCT` | 20% | SIMULATED | Grid storage standard |
| `BATTERY_MIN_KWH` | 124.8 kWh | Derived | — |
| `ENERGY_CRITICAL_THRESHOLD_KW` | −15.0 kW | SIMULATED | Hartwick et al. (2023) |
| `ENERGY_ALERT_THRESHOLD_KW` | −5.0 kW | SIMULATED | Hartwick et al. (2023) |
| `FORECAST_HORIZON_CYCLES` | 6 cycles | SIMULATED | 3 Martian sols |
| `FORECAST_MIN_CYCLES` | 4 cycles | SIMULATED | Welford (1962) |
