"""
Constants for the MGAB — Autonomous Base Management Module.

Every constant carries its source. Values marked SIMULATED have no direct
published reference for this exact configuration; justification is provided.

Colony baseline (all sizing decisions derive from this):
  - 6-person crew       — NASA DRA 5.0 (Drake, 2009); Hartwick et al., Nat. Astron. (2023)
  - 1 solar array       — arXiv:2410.00066: single 1,000 m² array, reference configuration
  - 2 wind turbines     — arXiv:2410.00066 (E33 reference) + 1 redundant unit (SIMULATED)
  - 2 battery units     — arXiv:2410.00066 (312 kWh reference) + 1 redundant unit (SIMULATED)
  - Colony location     — top-3 sites from Hartwick et al. (2023): diurnal avg wind > 24 kW

Energy balance (nominal, no degradation):
  Day   generation: 145 kW solar + 48 kW wind (2 x 24 kW) = 193 kW
  Day   consumption: 46 kW (all 8 modules active)
  Night generation: 20 kW wind (2 x 10 kW average)  OR  0 kW if wind < cut-in
  Night consumption: 30 kW (LSS + MED + HAB + PWR only)
  Battery usable: 2 x 312 x 0.80 = 499 kWh

Critical scenarios (realistic):
  - Night with wind < cut-in (< 10.3 m/s): E33 offline, battery drains 30 kW/h -> 16.6h autonomy
  - Storm + wind offline: solar 22 kW vs 46 kW -> CRITICAL in ~20h
  - Dust 80% + no wind (day): solar 29 kW vs 46 kW -> CRITICAL
  - --stress: global storm, battery drains ~378 kWh/night, CRITICAL in 1 sol

Source note on wind at night:
  NASA NTRS 19790057281 (Viking Lander 2 seismometer): "in all seasons nighttime conditions
  are usually very quiet" — low-wind nights are the norm, not the exception.
  The E33 cut-in of 10.3 m/s (arXiv:2410.00066) means the turbine is frequently
  offline at night, making battery the primary nocturnal energy source.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Simulation control
# ---------------------------------------------------------------------------

RANDOM_SEED: int = 42
# Fixed seed for reproducibility — ensures deterministic output across runs

SEPARATOR: str = "=" * 65
# Terminal output separator — shared across all display functions

# ---------------------------------------------------------------------------
# Colony configuration
# ---------------------------------------------------------------------------

COLONY_CREW_SIZE: int = 6
# NASA DRA 5.0 (Drake, 2009) — 6-person crew for long-stay Mars surface mission
# Hartwick et al., Nature Astronomy (2023): 24-35 kW total power for 6-crew, 500-sol mission

SOLAR_ARRAY_COUNT: int = 1
# arXiv:2410.00066 — single 1,000 m2 array, reference configuration for 6-person base
# Supports 32.1% of Martian surface locations when combined with 1 E33 and 312 kWh battery

WIND_TURBINE_COUNT: int = 2
# arXiv:2410.00066: 1 E33 turbine (reference unit)
# +1 redundant unit (SIMULATED) — single-failure tolerance; turbine offline at night is common

BATTERY_COUNT: int = 2
# arXiv:2410.00066: 1 battery of 312 kWh (reference unit)
# +1 redundant unit (SIMULATED) — degradation over 500-sol mission reduces effective capacity

# ---------------------------------------------------------------------------
# Colony location
# ---------------------------------------------------------------------------

COLONY_LOCATION: str = "Top-3 wind sites, Hartwick et al. (2023)"
# Hartwick et al., Nature Astronomy (2023): at 3 sites, E33 diurnal average wind power
# exceeds 24 kW at all simulated times throughout the year.
# Site selection based on wind energy availability is the methodology recommended by the paper.
# Specific site names are in the paper's Fig. 5 (behind paywall); cited as category.

# ---------------------------------------------------------------------------
# Day/night cycle (Martian sol ~24.6 h)
# ---------------------------------------------------------------------------

MARTIAN_DAY_HOURS: float = 12.0
# Approximate solar generation period per sol — NASA Mars Fact Sheet

MARTIAN_NIGHT_HOURS: float = 12.6
# Non-solar period per sol — NASA Mars Fact Sheet

# ---------------------------------------------------------------------------
# Solar energy
# ---------------------------------------------------------------------------

MARS_SOLAR_IRRADIANCE_WM2: float = 590.0
# NASA TM-102299, Appelbaum & Flood (1989) — top-of-atmosphere irradiance

MARS_SURFACE_IRRADIANCE_WM2: float = 500.0
# SIMULATED — 590 W/m2 minus ~15% atmospheric absorption
# Base reference: Levine et al. apud Power and Resources (2022)

SOLAR_PANEL_AREA_M2: float = 1000.0
# arXiv:2410.00066 — single array area for a six-person Mars base

SOLAR_PANEL_EFFICIENCY: float = 0.29
# SIMULATED — high-efficiency cells for space environment
# Reference: McMillon-Brown et al., ScienceDirect (2020)

SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE: float = 0.002
# 0.2%/Sol — Lorenz et al., Planetary and Space Science (2021)

SOLAR_DUST_ALERT_THRESHOLD: float = 0.30
# SIMULATED — operational alert threshold

SOLAR_DUST_CRITICAL_THRESHOLD: float = 0.60
# Reference: InSight lander — progressive accumulation without cleaning leads to power loss
# ScienceDirect (2024)

# ---------------------------------------------------------------------------
# Wind energy — Enercon E33
# ---------------------------------------------------------------------------

MARS_AIR_DENSITY_KGM3: float = 0.017
# arXiv:2410.00066 — Hybrid PV-Wind-Battery Power System for a Mars Base (2024)

WIND_TURBINE_DIAMETER_M: float = 33.4
# Enercon E33 — rotor diameter
# arXiv:2410.00066; Hartwick et al., Nature Astronomy (2023)

WIND_TURBINE_RATED_POWER_EARTH_KW: float = 330.0
# Enercon E33 rated output on Earth — manufacturer specification
# On Mars at best sites: ~24 kW diurnal average (Hartwick et al., 2023)

BETZ_LIMIT: float = 16 / 27
# Theoretical maximum turbine efficiency — Betz (1926)

WIND_TURBINE_EFFICIENCY: float = 0.35
# SIMULATED — lower bound of 35-50% of Betz limit; arXiv:2410.00066 uses manufacturer
# Cp curve scaled to Martian density. 0.35 is conservative approximation.

WIND_CUT_IN_MS: float = 10.3
# m/s on Mars — arXiv:2410.00066
# NOTE: Viking Lander data confirms nighttime winds are frequently below this threshold
# (NASA NTRS 19790057281). The E33 is often offline at night.

WIND_CUT_OUT_MS: float = 115.7
# m/s on Mars — arXiv:2410.00066

WIND_AVERAGE_POWER_KW_BEST_SITES: float = 24.0
# kW per E33 turbine, diurnal average, at top-3 wind sites
# Hartwick et al., Nature Astronomy (2023): "diurnal average wind power exceeds 24 kW"

WIND_AVERAGE_POWER_KW_GENERAL: float = 10.0
# kW per E33 turbine, planetary average
# Hartwick et al. (2023) / Interestingengineering.com (2023) citing the paper:
# "average power output of about 10 kW"

WIND_ABRASION_RATE_PER_CYCLE: float = 0.001
# SIMULATED — long-term blade degradation from abrasive Martian particles

WIND_ABRASION_ALERT_THRESHOLD: float = 0.25
# SIMULATED — operational alert threshold

# ---------------------------------------------------------------------------
# Battery — Enercon E33 reference system
# ---------------------------------------------------------------------------

BATTERY_CAPACITY_KWH: float = 312.0
# arXiv:2410.00066 — capacity per unit, reference system for 6-person base

BATTERY_MIN_PCT: float = 20.0
# SIMULATED — operational safety margin; prevents full discharge and cell damage

# ---------------------------------------------------------------------------
# Module consumption (nominal)
# ---------------------------------------------------------------------------
# Total day consumption: 46 kW
# Total night consumption: 30 kW
# Source anchor: Hartwick et al. (2023) — 24-35 kW total for 6-crew, 500-sol mission
# Distribution across modules: SIMULATED — proportional by criticality and function
# Night modules (LSS+MED+HAB+PWR) sum to 30 kW (lower bound of 24-35 kW range)
# Day-only modules (COM+SCI+LOG+MIN) add 16 kW operational load

LSS_CONSUMPTION_KW: float = 14.0
# SIMULATED — largest share of base load: air, pressure, water recycling, thermal control
# ~47% of 30 kW night base. No direct reference for isolated LSS in initial Mars mission.
# Hartwick (2023) 24-35 kW total implicitly includes LSS as the dominant consumer.

MED_CONSUMPTION_KW: float = 5.0
# SIMULATED — fixed medical infrastructure: monitoring, emergency systems
# ~17% of 30 kW night base.

HAB_CONSUMPTION_KW: float = 7.0
# SIMULATED — habitat HVAC, lighting, pressurization maintenance
# ~23% of 30 kW night base. Heating dominates in Martian cold (-60 C external nominal).

PWR_CONSUMPTION_KW: float = 4.0
# SIMULATED — power distribution, inverters, conversion losses
# ~13% of 30 kW night base.

COM_CONSUMPTION_KW: float = 3.0
# SIMULATED — antennas, transponders, Earth-Mars relay. Day-only operation.

SCI_CONSUMPTION_KW: float = 5.0
# SIMULATED — surface science laboratory. Day-only operation.

LOG_CONSUMPTION_KW: float = 3.0
# SIMULATED — rover charging, EVA support, pressurized storage. Day-only operation.

MIN_CONSUMPTION_KW: float = 5.0
# SIMULATED — ISRU basic: O2 and H2O extraction from regolith. Day-only operation.
# Full-scale ISRU (propellant production) reaches 100 kW (Space Science & Technology, 2021).
# Initial mission operates at ~5% of full scale.

# ---------------------------------------------------------------------------
# Decision thresholds
# ---------------------------------------------------------------------------

ENERGY_ALERT_THRESHOLD_KW: float = -5.0
# SIMULATED — negative balance triggering predictive alert (day) or watch (night)
# Scaled to consumption baseline: 46 kW day, 30 kW night

ENERGY_CRITICAL_THRESHOLD_KW: float = -15.0
# SIMULATED — balance triggering automatic module shutdown (day only)
# At this level, dust accumulation or equipment failure is causing real deficit

FORECAST_MIN_CYCLES: int = 4
# SIMULATED — minimum data points for reliable online regression

FORECAST_HORIZON_CYCLES: int = 6
# SIMULATED — look-ahead window for predictive alert (3 Martian sols)

CRITICAL_MODULE_PRIORITY_THRESHOLD: int = 3
# SIMULATED — modules with priority ≤ 3 (LSS, MED, HAB) receive immediate repair
# Critical life systems cannot be left degraded; repair is crew's first response

EQUIPMENT_FAILURE_MAX_CONSUMPTION_FACTOR: float = 2.0
# SIMULATED — failure cap at 2× nominal consumption to prevent runaway degradation

# ---------------------------------------------------------------------------
# Dust storm duration
# ---------------------------------------------------------------------------

DUST_STORM_MIN_DURATION_CYCLES: int = 6
# Minimum duration of a regional dust storm: 3 sols x 2 cycles/sol
# ScienceDirect (2022) — regional storm defined as duration > 3 sols

DUST_STORM_MAX_DURATION_CYCLES: int = 56
# Maximum duration of a regional dust storm: ~4 weeks = 56 cycles
# ScienceDirect (2022); lovethenightsky.com — regional storms last 1-2 weeks;

# ---------------------------------------------------------------------------
# Storm environment simulation
# ---------------------------------------------------------------------------

STORM_SOLAR_RESIDUAL_FACTOR: float = 0.05
# SIMULATED — minimum residual solar fraction during intense storm
# InSight lander: severe dust accumulation can reduce solar output by 95%+ (ScienceDirect, 2024)

STORM_WIND_DAY_MAX_FACTOR: float = 0.70
# SIMULATED — storm daytime wind capped at 70% of Viking-measured maximum

STORM_WIND_NIGHT_MAX_FACTOR: float = 0.60
# SIMULATED — storm nighttime wind reduced; Viking data: gusts, not sustained maximum

STORM_NIGHT_QUIET_PROBABILITY: float = 0.60
# SIMULATED — 60% chance of calm night even during active storm
# Consistent with NASA NTRS 19790057281: nighttime usually quiet across seasons

NIGHT_QUIET_PROBABILITY: float = 0.70
# NASA NTRS 19790057281 — Viking Lander 2: nighttime conditions usually very quiet
# Modeled as 70% probability of sub-cut-in wind speed (E33 offline)

NIGHT_WIND_MAX_FACTOR: float = 0.50
# SIMULATED — non-storm quiet night wind capped at 50% of maximum measured speed

# ---------------------------------------------------------------------------
# Sensor fallback defaults
# ---------------------------------------------------------------------------

WIND_SPEED_SENSOR_FALLBACK_MS: float = 15.0
# SIMULATED — fallback wind speed used when wind sensor returns None
# Representative daytime value above E33 cut-in (10.3 m/s); used in default scenario

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

MAINTENANCE_PROBABILITY_PER_CYCLE: float = 0.15
# SIMULATED — probability of maintenance being executed per cycle
# No direct reference; represents crew availability and task scheduling

EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT: float = 0.30
# SIMULATED — +30% consumption due to equipment failure

EQUIPMENT_FAILURE_DEGRADATION_RATE: float = 0.05
# SIMULATED — +5% additional consumption per cycle without maintenance

# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

MARS_EXTERNAL_TEMP_MIN_C: float = -125.0
# NASA Mars Fact Sheet

MARS_EXTERNAL_TEMP_MAX_C: float = 20.0
# NASA Mars Fact Sheet

COLONY_INTERNAL_TEMP_NOMINAL_C: float = 21.0
# SIMULATED — human thermal comfort standard

COLONY_INTERNAL_TEMP_MIN_C: float = 18.0
# SIMULATED

COLONY_INTERNAL_TEMP_MAX_C: float = 26.0
# SIMULATED

# ---------------------------------------------------------------------------
# Wind speed (environment simulation)
# ---------------------------------------------------------------------------

MARS_WIND_SPEED_MIN_MS: float = 2.0
# NASA PDS Viking Meteorology Data (VL1/VL2-M-MET-4-BINNED-P-T-V-V1.0)
# Calm conditions measured at both Viking lander sites

MARS_WIND_SPEED_MAX_MS: float = 30.0
# NASA PDS Viking Meteorology Data — peak storm winds at Viking lander sites

MARS_WIND_STORM_MIN_MS: float = 17.0
# ScienceDirect, Perez-Prada et al. (2021) — wind as backup energy source for Mars missions;
# uses Viking Lander 2 data (1050 sols). Storm-season winds consistently above this threshold.

MARS_WIND_NIGHT_TYPICAL_MS: float = 5.0
# NASA NTRS 19790057281 (Viking Lander 2 seismometer analysis):
# "in all seasons nighttime conditions are usually very quiet"
# Represented as 5 m/s — below E33 cut-in of 10.3 m/s, turbine offline most nights.

# ---------------------------------------------------------------------------
# Derived constants (computed once; never used as magic numbers in formulas)
# ---------------------------------------------------------------------------

WIND_TURBINE_SWEPT_AREA_M2: float = math.pi * (WIND_TURBINE_DIAMETER_M / 2) ** 2
# E33 rotor swept area — derived from WIND_TURBINE_DIAMETER_M

BATTERY_TOTAL_CAPACITY_KWH: float = BATTERY_CAPACITY_KWH * BATTERY_COUNT
# Total battery bank capacity — BATTERY_CAPACITY_KWH x BATTERY_COUNT

BATTERY_MIN_KWH: float = BATTERY_TOTAL_CAPACITY_KWH * (BATTERY_MIN_PCT / 100)
# Minimum battery reserve in kWh — safety margin below which CRITICAL is triggered

WIND_CALM_UPPER_MS: float = WIND_CUT_IN_MS * 0.90
# Upper bound for calm wind simulation — set just below E33 cut-in speed (SIMULATED)
