"""
Simulation loop for the MGAB — Autonomous Base Management Module.

Orchestrates one full simulation run:
  For each cycle:
    1. Advance time (cycle counter, day/night toggle)
    2. Update environment (variation or persistent storm)
    3. Optionally inject anomaly
    4. Update energy state
    5. Update forecast regressions
    6. Apply decision logic
    7. Report cycle state

No day/night module schedule — all modules operate continuously (24h).
Night energy deficit is purely physics-driven:
  - E33 offline when wind < cut-in (10.3 m/s) — common at night
  - Solar = 0 at night
  - Battery covers deficit; CRITICAL if depleted before dawn

Dust storm model:
  Regional storms last 6-56 cycles (ScienceDirect, 2022).
  During storm: solar irradiance reduced, wind elevated during day,
  wind can drop below cut-in at night even during storms
  (NASA NTRS 19790057281: nighttime conditions usually quiet).
"""

import random

from src.constants import (
    DUST_STORM_MAX_DURATION_CYCLES,
    DUST_STORM_MIN_DURATION_CYCLES,
    MARS_SURFACE_IRRADIANCE_WM2,
    MARS_WIND_SPEED_MAX_MS,
    MARS_WIND_SPEED_MIN_MS,
    MARS_WIND_STORM_MIN_MS,
    NIGHT_QUIET_PROBABILITY,
    NIGHT_WIND_MAX_FACTOR,
    STORM_NIGHT_QUIET_PROBABILITY,
    STORM_SOLAR_RESIDUAL_FACTOR,
    STORM_WIND_DAY_MAX_FACTOR,
    STORM_WIND_NIGHT_MAX_FACTOR,
    WIND_CALM_UPPER_MS,
)
from src.decision import (
    apply_anomaly_equipment_failure,
    apply_anomaly_sensor_error,
    apply_decision,
)
from src.energy import update_energy_state
from src.enums import AnomalyType
from src.forecast import update_forecast
from src.models import ColonyState
from src.report import display_cycle_report, display_final_report


def _update_environment(state: ColonyState) -> None:
    """
    Apply environmental variation for the current cycle.

    Storm active: solar reduced, daytime wind elevated, night wind can drop below cut-in.
    No storm: mild variation; night wind biased toward quiet (Viking Lander observations).
    """
    if state.active_storm_cycles_remaining > 0:
        intensity = state.environment.dust_storm_intensity

        if state.is_daytime:
            reduction = intensity * 0.85
            state.environment.solar_irradiance_wm2 = max(
                MARS_SURFACE_IRRADIANCE_WM2 * STORM_SOLAR_RESIDUAL_FACTOR,
                MARS_SURFACE_IRRADIANCE_WM2 * (1.0 - reduction),
            )
            # Daytime storm: wind elevated but varies
            state.environment.wind_speed_ms = random.uniform(
                MARS_WIND_STORM_MIN_MS,
                MARS_WIND_SPEED_MAX_MS * STORM_WIND_DAY_MAX_FACTOR,
            )
        else:
            state.environment.solar_irradiance_wm2 = None
            # Night during storm: can still drop below cut-in
            # NASA NTRS 19790057281: nighttime quiet even in storm season
            if random.random() < STORM_NIGHT_QUIET_PROBABILITY:
                state.environment.wind_speed_ms = random.uniform(
                    MARS_WIND_SPEED_MIN_MS,
                    WIND_CALM_UPPER_MS,
                )
            else:
                state.environment.wind_speed_ms = random.uniform(
                    MARS_WIND_STORM_MIN_MS,
                    MARS_WIND_SPEED_MAX_MS * STORM_WIND_NIGHT_MAX_FACTOR,
                )

        state.active_storm_cycles_remaining -= 1

    else:
        state.environment.dust_storm_intensity = 0.0

        if state.is_daytime:
            # Daytime: mild wind variation
            if state.environment.wind_speed_ms is not None:
                new_wind = state.environment.wind_speed_ms + random.uniform(-2.0, 2.0)
                state.environment.wind_speed_ms = max(
                    MARS_WIND_SPEED_MIN_MS, min(MARS_WIND_SPEED_MAX_MS, new_wind)
                )
            # Solar: mild irradiance variation
            base = state.last_valid_solar_irradiance_wm2
            new_irr = base + random.uniform(-20.0, 20.0)
            state.environment.solar_irradiance_wm2 = max(
                MARS_SURFACE_IRRADIANCE_WM2 * 0.5,
                min(MARS_SURFACE_IRRADIANCE_WM2, new_irr),
            )
        else:
            state.environment.solar_irradiance_wm2 = None
            # Night: wind usually quiet (NASA NTRS 19790057281)
            # 70% below cut-in (E33 offline), 30% operational
            if random.random() < NIGHT_QUIET_PROBABILITY:
                state.environment.wind_speed_ms = random.uniform(
                    MARS_WIND_SPEED_MIN_MS,
                    WIND_CALM_UPPER_MS,
                )
            else:
                state.environment.wind_speed_ms = random.uniform(
                    WIND_CALM_UPPER_MS,
                    MARS_WIND_SPEED_MAX_MS * NIGHT_WIND_MAX_FACTOR,
                )


def inject_anomaly(state: ColonyState, anomaly_probability: float) -> None:
    """
    Randomly inject an anomaly this cycle.

    DUST_STORM: sets duration (6-56 cycles) and intensity. No reset if already active.
    EQUIPMENT_FAILURE: increases one module's consumption by 30%.
    SENSOR_ERROR: sets wind or solar sensor to None for one cycle.
    """
    if random.random() > anomaly_probability:
        return

    anomaly_type = random.choice(list(AnomalyType))

    if anomaly_type == AnomalyType.DUST_STORM:
        if state.active_storm_cycles_remaining > 0:
            return
        duration = random.randint(DUST_STORM_MIN_DURATION_CYCLES, DUST_STORM_MAX_DURATION_CYCLES)
        intensity = random.uniform(0.3, 1.0)
        state.environment.dust_storm_intensity = intensity
        state.active_storm_cycles_remaining = duration

    elif anomaly_type == AnomalyType.EQUIPMENT_FAILURE:
        module_name = random.choice(state.modules).name
        apply_anomaly_equipment_failure(state, module_name)

    elif anomaly_type == AnomalyType.SENSOR_ERROR:
        sensor = random.choice(["wind", "solar"])
        apply_anomaly_sensor_error(state, sensor)


def run_simulation(
    state: ColonyState,
    cycles: int,
    anomaly_probability: float = 0.0,
) -> None:
    """
    Run the full simulation for the given number of cycles.

    Each cycle represents one half-sol (~12 h), alternating day and night.
    """
    for _ in range(cycles):
        state.cycle += 1
        state.is_daytime = not state.is_daytime

        _update_environment(state)

        if anomaly_probability > 0.0:
            inject_anomaly(state, anomaly_probability)

        update_energy_state(state)
        update_forecast(state)
        apply_decision(state)
        display_cycle_report(state)

    display_final_report(state)
