from __future__ import annotations

import math

# -- Simulation control --

RANDOM_SEED: int = 42       # fixed seed — deterministic output across runs
SEPARATOR: str = "=" * 65   # terminal separator shared across display functions

# -- Colony configuration --

COLONY_CREW_SIZE: int = 6
# NASA DRA 5.0 (Drake, 2009) — 6-person crew; Hartwick et al., Nat. Astron. (2023)

SOLAR_ARRAY_COUNT: int = 1
# arXiv:2410.00066 — single 1,000 m² array, reference config for 6-person base

WIND_TURBINE_COUNT: int = 2
# arXiv:2410.00066: 1 E33 (reference) + 1 redundant unit (SIMULATED)

BATTERY_COUNT: int = 2
# arXiv:2410.00066: 1 battery 312 kWh (reference) + 1 redundant unit (SIMULATED)

# -- Colony location --

COLONY_LOCATION: str = "Top-3 wind sites, Hartwick et al. (2023)"
# Hartwick et al., Nature Astronomy (2023): E33 diurnal avg > 24 kW at all simulated times

# -- Day/night cycle (Martian sol ~24.6 h) --

MARTIAN_DAY_HOURS: float = 12.0     # NASA Mars Fact Sheet
MARTIAN_NIGHT_HOURS: float = 12.6   # NASA Mars Fact Sheet

# -- Solar energy --

MARS_SOLAR_IRRADIANCE_WM2: float = 590.0
# NASA TM-102299, Appelbaum & Flood (1989) — top-of-atmosphere irradiance

MARS_SURFACE_IRRADIANCE_WM2: float = 500.0
# SIMULATED — 590 W/m² minus ~15% atmospheric absorption

SOLAR_PANEL_AREA_M2: float = 1000.0       # arXiv:2410.00066
SOLAR_PANEL_EFFICIENCY: float = 0.29
# SIMULATED — high-efficiency cells; McMillon-Brown et al., ScienceDirect (2020)

SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE: float = 0.002
# 0.2%/Sol — Lorenz et al., Planetary and Space Science (2021)

SOLAR_DUST_ALERT_THRESHOLD: float = 0.30    # SIMULATED — operational alert threshold
SOLAR_DUST_CRITICAL_THRESHOLD: float = 0.60
# InSight lander: progressive accumulation leads to power loss (ScienceDirect, 2024)

# -- Wind energy — Enercon E33 --

MARS_AIR_DENSITY_KGM3: float = 0.017              # arXiv:2410.00066
WIND_TURBINE_DIAMETER_M: float = 33.4             # Enercon E33; arXiv:2410.00066
WIND_TURBINE_RATED_POWER_EARTH_KW: float = 330.0  # Enercon E33 — manufacturer spec
BETZ_LIMIT: float = 16 / 27                       # Betz (1926) — theoretical max efficiency
WIND_TURBINE_EFFICIENCY: float = 0.35
# SIMULATED — conservative 35% of Betz limit; arXiv:2410.00066 uses full Cp curve

WIND_CUT_IN_MS: float = 10.3    # m/s on Mars — arXiv:2410.00066
WIND_CUT_OUT_MS: float = 115.7  # m/s on Mars — arXiv:2410.00066

WIND_AVERAGE_POWER_KW_BEST_SITES: float = 24.0
# kW/turbine diurnal avg at top-3 sites — Hartwick et al., Nature Astronomy (2023)

WIND_AVERAGE_POWER_KW_GENERAL: float = 10.0
# kW/turbine planetary average — Hartwick et al. (2023)

WIND_ABRASION_RATE_PER_CYCLE: float = 0.001   # SIMULATED — Martian abrasive particle degradation
WIND_ABRASION_ALERT_THRESHOLD: float = 0.25   # SIMULATED — operational alert threshold

# -- Battery --

BATTERY_CAPACITY_KWH: float = 312.0   # arXiv:2410.00066 — capacity per unit
BATTERY_MIN_PCT: float = 20.0         # SIMULATED — safety margin; prevents full discharge

# -- Module consumption (nominal) --
# Total: 46 kW — all 8 modules operate 24h (CELSS, NIH 2019; NASA ECLSS NTRS 20230002103)
# Source anchor: Hartwick et al. (2023) — 24-35 kW for 6-crew, 500-sol mission
# Distribution: SIMULATED — proportional by criticality and function

LSS_CONSUMPTION_KW: float = 14.0   # SIMULATED — air, pressure, water recycling, thermal control
MED_CONSUMPTION_KW: float = 5.0    # SIMULATED — fixed medical infrastructure
HAB_CONSUMPTION_KW: float = 7.0    # SIMULATED — habitat HVAC, lighting, pressurization
PWR_CONSUMPTION_KW: float = 4.0    # SIMULATED — power distribution, inverters, conversion losses
COM_CONSUMPTION_KW: float = 3.0    # SIMULATED — antennas, transponders, Earth-Mars relay
SCI_CONSUMPTION_KW: float = 5.0    # SIMULATED — surface science laboratory
LOG_CONSUMPTION_KW: float = 3.0    # SIMULATED — rover charging, EVA support, storage
MIN_CONSUMPTION_KW: float = 5.0    # SIMULATED — ISRU basic: O₂ and H₂O extraction

# -- Decision thresholds --

ENERGY_ALERT_THRESHOLD_KW: float = -5.0      # SIMULATED — negative balance triggering predictive alert
ENERGY_CRITICAL_THRESHOLD_KW: float = -15.0  # SIMULATED — balance triggering automatic shutdown (day)
FORECAST_MIN_CYCLES: int = 4                 # SIMULATED — minimum data points for reliable regression
FORECAST_HORIZON_CYCLES: int = 6             # SIMULATED — look-ahead window (3 Martian sols)
CRITICAL_MODULE_PRIORITY_THRESHOLD: int = 3  # SIMULATED — priority ≤ 3 receives immediate repair
EQUIPMENT_FAILURE_MAX_CONSUMPTION_FACTOR: float = 2.0  # SIMULATED — cap at 2× nominal

# -- Dust storm duration --

DUST_STORM_MIN_DURATION_CYCLES: int = 6
# Regional storm minimum: 3 sols × 2 cycles/sol — ScienceDirect (2022)

DUST_STORM_MAX_DURATION_CYCLES: int = 56
# Regional storm maximum: ~4 weeks — ScienceDirect (2022)

# -- Storm environment simulation --

STORM_SOLAR_RESIDUAL_FACTOR: float = 0.05
# SIMULATED — min solar fraction during intense storm; InSight: 95%+ loss (ScienceDirect, 2024)

STORM_WIND_DAY_MAX_FACTOR: float = 0.70    # SIMULATED — storm daytime wind capped at 70% of max
STORM_WIND_NIGHT_MAX_FACTOR: float = 0.60  # SIMULATED — storm nighttime wind reduced
STORM_NIGHT_QUIET_PROBABILITY: float = 0.60
# SIMULATED — 60% calm nights even during storm; NASA NTRS 19790057281

NIGHT_QUIET_PROBABILITY: float = 0.70
# NASA NTRS 19790057281 — Viking Lander 2: nighttime usually very quiet; 70% below cut-in

NIGHT_WIND_MAX_FACTOR: float = 0.50   # SIMULATED — quiet night wind capped at 50% of max

# -- Sensor fallback defaults --

WIND_SPEED_SENSOR_FALLBACK_MS: float = 15.0
# SIMULATED — fallback when wind sensor returns None; above E33 cut-in (default scenario)

# -- Maintenance --

MAINTENANCE_PROBABILITY_PER_CYCLE: float = 0.15          # SIMULATED — crew availability per cycle
EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT: float = 0.30  # SIMULATED — +30% consumption on failure
EQUIPMENT_FAILURE_DEGRADATION_RATE: float = 0.05          # SIMULATED — +5%/cycle without repair

# -- Temperature --

MARS_EXTERNAL_TEMP_MIN_C: float = -125.0      # NASA Mars Fact Sheet
MARS_EXTERNAL_TEMP_MAX_C: float = 20.0        # NASA Mars Fact Sheet
COLONY_INTERNAL_TEMP_NOMINAL_C: float = 21.0  # SIMULATED — human thermal comfort
COLONY_INTERNAL_TEMP_MIN_C: float = 18.0      # SIMULATED
COLONY_INTERNAL_TEMP_MAX_C: float = 26.0      # SIMULATED

# -- Wind speed (environment simulation) --

MARS_WIND_SPEED_MIN_MS: float = 2.0
# NASA PDS Viking Meteorology Data — calm conditions at both lander sites

MARS_WIND_SPEED_MAX_MS: float = 30.0
# NASA PDS Viking Meteorology Data — peak storm winds

MARS_WIND_STORM_MIN_MS: float = 17.0
# ScienceDirect, Perez-Prada et al. (2021) — storm-season threshold (Viking Lander 2)

MARS_WIND_NIGHT_TYPICAL_MS: float = 5.0
# NASA NTRS 19790057281 — "nighttime conditions usually very quiet"; below E33 cut-in

# -- Derived constants --

WIND_TURBINE_SWEPT_AREA_M2: float = math.pi * (WIND_TURBINE_DIAMETER_M / 2) ** 2
BATTERY_TOTAL_CAPACITY_KWH: float = BATTERY_CAPACITY_KWH * BATTERY_COUNT
BATTERY_MIN_KWH: float = BATTERY_TOTAL_CAPACITY_KWH * (BATTERY_MIN_PCT / 100)
WIND_CALM_UPPER_MS: float = WIND_CUT_IN_MS * 0.90   # SIMULATED — just below E33 cut-in
