"""
Scenarios for the MGAB — Autonomous Base Management Module.

Each scenario function returns a fully initialized ColonyState.

Colony location: top-3 wind sites from Hartwick et al., Nature Astronomy (2023).
At these sites, E33 diurnal average wind power exceeds 24 kW at all simulated times.

Colony crew composition (NASA DRA 5.0, Drake 2009):
  1. Commander        -> COM-01 Communications
  2. Pilot            -> LOG-01 Logistics (rovers, EVA)
  3. Medical Officer  -> MED-01 Medical
  4. Scientist        -> SCI-01 Science Lab
  5. Engineer ECLSS   -> LSS-01 Life Support + HAB-01 Habitat (shared infrastructure)
  6. Engineer Power   -> PWR-01 Power Systems + MIN-01 ISRU Mining (shared energy domain)

Module operation model:
  All 8 modules operate continuously (24h), totaling 46 kW.
  Source: life support systems "controlled automatically" (CELSS study, NIH 2019);
  NASA ECLSS (NTRS 20230002103): "automation to reduce regular maintenance time";
  Space S&T (2021): ISRU can operate in 24h or 8h modes — energy-driven, not crew-driven.

  Night energy deficit is covered by battery when E33 is offline (wind < cut-in).
  E33 cut-in: 10.3 m/s. NASA NTRS 19790057281: "nighttime conditions usually very quiet."
  70% of nights: E33 offline. Battery (499 kWh usable) covers 10.9h at 46 kW.
  Without wind: CRITICAL before dawn. With wind: 19.2h autonomy. Realistic behavior.
"""

import random
from collections import deque

from src.constants import (
    BATTERY_TOTAL_CAPACITY_KWH,
    COLONY_INTERNAL_TEMP_NOMINAL_C,
    COM_CONSUMPTION_KW,
    HAB_CONSUMPTION_KW,
    LOG_CONSUMPTION_KW,
    LSS_CONSUMPTION_KW,
    MARS_EXTERNAL_TEMP_MAX_C,
    MARS_EXTERNAL_TEMP_MIN_C,
    MARS_SURFACE_IRRADIANCE_WM2,
    MARS_WIND_SPEED_MAX_MS,
    MARS_WIND_SPEED_MIN_MS,
    MED_CONSUMPTION_KW,
    MIN_CONSUMPTION_KW,
    PWR_CONSUMPTION_KW,
    SCI_CONSUMPTION_KW,
    WIND_CUT_IN_MS,
    WIND_SPEED_SENSOR_FALLBACK_MS,
)
from src.enums import ModuleName, SystemStatus
from src.models import (
    ColonyState,
    EnvironmentReading,
    EnergyState,
    ForecastState,
    Module,
    OnlineRegression,
)


def _build_default_modules() -> list:
    """
    Build the eight colony modules at nominal consumption, all active 24h.

    Priority 1 = critical (never shuts down for energy reasons).
    Higher number = first to shut down when battery is depleted.
    All modules operate continuously — shutdown is energy-driven, not schedule-driven.
    """
    return [
        Module(
            name=ModuleName.LIFE_SUPPORT.value,
            nominal_consumption_kw=LSS_CONSUMPTION_KW,
            current_consumption_kw=LSS_CONSUMPTION_KW,
            priority=1,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.MEDICAL.value,
            nominal_consumption_kw=MED_CONSUMPTION_KW,
            current_consumption_kw=MED_CONSUMPTION_KW,
            priority=2,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.HABITAT.value,
            nominal_consumption_kw=HAB_CONSUMPTION_KW,
            current_consumption_kw=HAB_CONSUMPTION_KW,
            priority=3,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.POWER_SYSTEMS.value,
            nominal_consumption_kw=PWR_CONSUMPTION_KW,
            current_consumption_kw=PWR_CONSUMPTION_KW,
            priority=4,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.COMMUNICATIONS.value,
            nominal_consumption_kw=COM_CONSUMPTION_KW,
            current_consumption_kw=COM_CONSUMPTION_KW,
            priority=5,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.SCIENCE.value,
            nominal_consumption_kw=SCI_CONSUMPTION_KW,
            current_consumption_kw=SCI_CONSUMPTION_KW,
            priority=6,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.LOGISTICS.value,
            nominal_consumption_kw=LOG_CONSUMPTION_KW,
            current_consumption_kw=LOG_CONSUMPTION_KW,
            priority=7,
            active=True,
            sensor_operational=True,
        ),
        Module(
            name=ModuleName.MINING.value,
            nominal_consumption_kw=MIN_CONSUMPTION_KW,
            current_consumption_kw=MIN_CONSUMPTION_KW,
            priority=8,
            active=True,
            sensor_operational=True,
        ),
    ]


def default_scenario() -> ColonyState:
    """
    Fixed, deterministic starting conditions.

    Starts at daytime cycle 0. Battery at full capacity.
    Wind at 15 m/s — above E33 cut-in, realistic daytime value.
    No dust accumulation, no blade abrasion, no anomalies.
    """
    modules = _build_default_modules()
    total_consumption_kw = sum(m.current_consumption_kw for m in modules)

    environment = EnvironmentReading(
        wind_speed_ms=WIND_SPEED_SENSOR_FALLBACK_MS,
        solar_irradiance_wm2=MARS_SURFACE_IRRADIANCE_WM2,
        internal_temperature_c=COLONY_INTERNAL_TEMP_NOMINAL_C,
        external_temperature_c=-60.0,
        dust_storm_intensity=0.0,
    )

    energy = EnergyState(
        solar_generation_kw=0.0,
        wind_generation_kw=0.0,
        total_consumption_kw=total_consumption_kw,
        battery_reserve_kwh=BATTERY_TOTAL_CAPACITY_KWH,
        solar_dust_accumulation=0.0,
        wind_blade_abrasion=0.0,
    )

    return ColonyState(
        cycle=0,
        is_daytime=True,
        environment=environment,
        energy=energy,
        modules=modules,
        forecast=ForecastState(
            wind_to_generation=OnlineRegression(),
            cycle_to_balance=OnlineRegression(),
        ),
        status=SystemStatus.OPERATIONAL,
        energy_history=[],
        wind_history=[],
        dust_history=[],
        alert_queue=deque(),
        active_storm_cycles_remaining=0,
        last_valid_solar_irradiance_wm2=MARS_SURFACE_IRRADIANCE_WM2,
        last_valid_wind_speed_ms=WIND_SPEED_SENSOR_FALLBACK_MS,
    )


def random_scenario() -> ColonyState:
    """
    Randomized starting conditions within realistic Martian ranges.

    Wind speed drawn from Martian range (Viking Lander data, NASA PDS).
    Night wind biased toward quiet conditions (NASA NTRS 19790057281).
    Battery starts between 50-100%; dust accumulation 0-20%.
    """
    is_daytime = random.choice([True, False])

    if is_daytime:
        wind_speed_ms = random.uniform(MARS_WIND_SPEED_MIN_MS, MARS_WIND_SPEED_MAX_MS)
        solar_irradiance_wm2 = random.uniform(
            MARS_SURFACE_IRRADIANCE_WM2 * 0.6,
            MARS_SURFACE_IRRADIANCE_WM2,
        )
    else:
        # Night: biased toward quiet — E33 typically offline
        wind_speed_ms = random.uniform(MARS_WIND_SPEED_MIN_MS, MARS_WIND_SPEED_MAX_MS * 0.6)
        solar_irradiance_wm2 = None

    external_temperature_c = random.uniform(MARS_EXTERNAL_TEMP_MIN_C, MARS_EXTERNAL_TEMP_MAX_C)
    battery_start_kwh = random.uniform(
        BATTERY_TOTAL_CAPACITY_KWH * 0.5,
        BATTERY_TOTAL_CAPACITY_KWH,
    )
    solar_dust_start = random.uniform(0.0, 0.20)

    modules = _build_default_modules()
    total_consumption_kw = sum(m.current_consumption_kw for m in modules)

    environment = EnvironmentReading(
        wind_speed_ms=wind_speed_ms,
        solar_irradiance_wm2=solar_irradiance_wm2,
        internal_temperature_c=COLONY_INTERNAL_TEMP_NOMINAL_C,
        external_temperature_c=external_temperature_c,
        dust_storm_intensity=0.0,
    )

    energy = EnergyState(
        solar_generation_kw=0.0,
        wind_generation_kw=0.0,
        total_consumption_kw=total_consumption_kw,
        battery_reserve_kwh=battery_start_kwh,
        solar_dust_accumulation=solar_dust_start,
        wind_blade_abrasion=0.0,
    )

    return ColonyState(
        cycle=0,
        is_daytime=is_daytime,
        environment=environment,
        energy=energy,
        modules=modules,
        forecast=ForecastState(
            wind_to_generation=OnlineRegression(),
            cycle_to_balance=OnlineRegression(),
        ),
        status=SystemStatus.OPERATIONAL,
        energy_history=[],
        wind_history=[],
        dust_history=[],
        alert_queue=deque(),
        active_storm_cycles_remaining=0,
        last_valid_solar_irradiance_wm2=solar_irradiance_wm2 or MARS_SURFACE_IRRADIANCE_WM2,
        last_valid_wind_speed_ms=wind_speed_ms or WIND_SPEED_SENSOR_FALLBACK_MS,
    )
