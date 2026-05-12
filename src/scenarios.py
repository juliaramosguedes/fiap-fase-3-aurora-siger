from __future__ import annotations

import random
from collections import deque

from .constants import (
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
from .enums import ModuleName, SystemStatus
from .models import (
    ColonyState,
    EnvironmentReading,
    EnergyState,
    ForecastState,
    Module,
    OnlineRegression,
)


def _build_default_modules() -> list[Module]:
    """Eight colony modules at nominal consumption, all active 24h. Shutdown is energy-driven."""
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
    """Fixed deterministic start: daytime, full battery, 15 m/s wind, no degradation."""
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
    """Randomized start within Martian ranges. Battery 50-100%, dust 0-20%, night wind biased quiet."""
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
