"""
Energy calculations for the MGAB — Autonomous Base Management Module.

Covers:
- Solar generation (irradiance, panel efficiency, dust degradation, array count)
- Wind generation (Betz power equation, cut-in/cut-out, blade abrasion, turbine count)
- Battery charge/discharge management (total bank capacity)
- Dust and abrasion accumulation per cycle
- Day/night cycle: solar generation is zero at night; wind runs continuously

Formula note — solar generation per array:
  solar_kw = AREA_m2 x irradiance_Wm2 x EFFICIENCY x (1 - dust) / 1000
  Division by 1000 converts W to kW.
  Total = single_array_kw x SOLAR_ARRAY_COUNT
  Nominal: 1000 x 500 x 0.29 / 1000 x 1 array = 145 kW

Formula note — wind generation per turbine:
  wind_kw = 0.5 x rho x swept_area x v^3 x efficiency x (1 - abrasion) / 1000
  Total = single_turbine_kw x WIND_TURBINE_COUNT
  Nominal at 15 m/s: ~8.8 kW/turbine x 2 turbines = 17.6 kW
"""

from __future__ import annotations

from .constants import (
    BATTERY_MIN_KWH,
    BATTERY_TOTAL_CAPACITY_KWH,
    MARS_AIR_DENSITY_KGM3,
    SOLAR_ARRAY_COUNT,
    SOLAR_DUST_ALERT_THRESHOLD,
    SOLAR_DUST_CRITICAL_THRESHOLD,
    SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE,
    SOLAR_PANEL_AREA_M2,
    SOLAR_PANEL_EFFICIENCY,
    WIND_ABRASION_ALERT_THRESHOLD,
    WIND_ABRASION_RATE_PER_CYCLE,
    WIND_CUT_IN_MS,
    WIND_CUT_OUT_MS,
    WIND_TURBINE_COUNT,
    WIND_TURBINE_EFFICIENCY,
    WIND_TURBINE_SWEPT_AREA_M2,
)
from .alerts import enqueue_alert
from .enums import AlertType
from .models import ColonyState


# ---------------------------------------------------------------------------
# Solar generation
# ---------------------------------------------------------------------------


def compute_solar_generation_kw(
    solar_irradiance_wm2: float,
    solar_dust_accumulation: float,
) -> float:
    """
    Total solar power output in kW across all arrays.

    P = AREA x irradiance x EFFICIENCY x (1 - dust) / 1000 x ARRAY_COUNT
    Returns 0.0 at night (caller passes 0.0 irradiance when is_daytime is False).
    Source: adapted from arXiv:2410.00066 (2024).
    """
    single_array_kw = (
        SOLAR_PANEL_AREA_M2
        * solar_irradiance_wm2
        * SOLAR_PANEL_EFFICIENCY
        * (1.0 - solar_dust_accumulation)
        / 1000.0
    )
    return single_array_kw * SOLAR_ARRAY_COUNT


# ---------------------------------------------------------------------------
# Wind generation
# ---------------------------------------------------------------------------


def compute_wind_generation_kw(
    wind_speed_ms: float,
    wind_blade_abrasion: float,
) -> float:
    """
    Total wind power output in kW across all turbines.

    P = 0.5 x rho x A x v^3 x efficiency x (1 - abrasion) / 1000 x TURBINE_COUNT
    Returns 0.0 outside cut-in / cut-out range.
    Runs day and night — wind is not sun-dependent.
    Source: Betz (1926); arXiv:2410.00066 (2024).
    """
    if wind_speed_ms < WIND_CUT_IN_MS or wind_speed_ms > WIND_CUT_OUT_MS:
        return 0.0

    single_turbine_kw = (
        0.5
        * MARS_AIR_DENSITY_KGM3
        * WIND_TURBINE_SWEPT_AREA_M2
        * wind_speed_ms ** 3
        * WIND_TURBINE_EFFICIENCY
        * (1.0 - wind_blade_abrasion)
        / 1000.0
    )
    return single_turbine_kw * WIND_TURBINE_COUNT


# ---------------------------------------------------------------------------
# Dust and abrasion accumulation
# ---------------------------------------------------------------------------


def accumulate_solar_dust(
    current_accumulation: float,
    dust_storm_intensity: float,
) -> float:
    """
    New solar dust accumulation factor after one cycle.

    Base rate increases with storm intensity. Capped at 1.0.
    Source: Lorenz et al., Planetary and Space Science (2021).
    """
    increase = SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE * (1.0 + dust_storm_intensity)
    return min(1.0, current_accumulation + increase)


def accumulate_wind_abrasion(current_abrasion: float) -> float:
    """
    New wind blade abrasion factor after one cycle.

    Constant rate; storms do not accelerate abrasion
    (abrasive particle mass flux is the limiting factor, not wind speed alone).
    Capped at 1.0.
    Source: SIMULATED — no direct published rate for Martian turbine blades.
    """
    return min(1.0, current_abrasion + WIND_ABRASION_RATE_PER_CYCLE)


def perform_solar_maintenance() -> float:
    """Reset dust accumulation to zero. Simulates full panel cleaning by crew."""
    return 0.0


def perform_wind_maintenance() -> float:
    """Reset blade abrasion to zero. Simulates full blade servicing by crew."""
    return 0.0


# ---------------------------------------------------------------------------
# Battery management
# ---------------------------------------------------------------------------


def update_battery(
    battery_reserve_kwh: float,
    balance_kw: float,
) -> float:
    """
    Charge or discharge the battery bank based on energy balance.

    Positive balance charges up to total bank capacity.
    Negative balance draws down to zero.
    Decision logic (module shutdown when battery is depleted) lives in decision.py.
    """
    updated = battery_reserve_kwh + balance_kw
    return max(0.0, min(BATTERY_TOTAL_CAPACITY_KWH, updated))


# ---------------------------------------------------------------------------
# Consumption aggregation
# ---------------------------------------------------------------------------


def compute_total_consumption_kw(modules: list) -> float:
    """Sum of current_consumption_kw across all active modules."""
    return sum(m.current_consumption_kw for m in modules if m.active)


# ---------------------------------------------------------------------------
# Main energy update — called once per cycle
# ---------------------------------------------------------------------------


def update_energy_state(state: ColonyState) -> None:
    """
    Recompute the full energy state for the current cycle.

    Mutates state.energy in place:
    - solar generation: zero at night; computed from irradiance during day
    - wind generation: computed every cycle (day and night)
    - total consumption: sum of active modules only
    - dust and abrasion accumulation
    - battery charge/discharge

    Uses last valid sensor reading when current reading is None (sensor_error).
    Appends alerts to state.alert_queue when degradation thresholds are crossed.
    """
    env = state.environment
    energy = state.energy

    # --- Resolve wind sensor (fallback on None) ---
    if env.wind_speed_ms is not None:
        wind_speed = env.wind_speed_ms
        state.last_valid_wind_speed_ms = wind_speed
    else:
        wind_speed = state.last_valid_wind_speed_ms
        enqueue_alert(
            state, AlertType.SENSOR_ERROR,
            "Sensor de velocidade do vento offline — usando última leitura válida",
        )

    # --- Resolve solar sensor (only relevant during day) ---
    if state.is_daytime:
        if env.solar_irradiance_wm2 is not None:
            solar_irradiance = env.solar_irradiance_wm2
            state.last_valid_solar_irradiance_wm2 = solar_irradiance
        else:
            solar_irradiance = state.last_valid_solar_irradiance_wm2
            enqueue_alert(
                state, AlertType.SENSOR_ERROR,
                "Sensor de irradiância solar offline — usando última leitura válida",
            )
    else:
        solar_irradiance = 0.0   # night: no solar input regardless of sensor state

    # --- Accumulate degradation (every cycle, day and night) ---
    energy.solar_dust_accumulation = accumulate_solar_dust(
        energy.solar_dust_accumulation,
        env.dust_storm_intensity,
    )
    energy.wind_blade_abrasion = accumulate_wind_abrasion(energy.wind_blade_abrasion)

    # --- Degradation alerts ---
    if energy.solar_dust_accumulation >= SOLAR_DUST_CRITICAL_THRESHOLD:
        enqueue_alert(
            state, AlertType.DUST_ACCUMULATION,
            f"Acúmulo crítico de poeira: {energy.solar_dust_accumulation:.1%} — manutenção imediata necessária",
        )
    elif energy.solar_dust_accumulation >= SOLAR_DUST_ALERT_THRESHOLD:
        enqueue_alert(
            state, AlertType.DUST_ACCUMULATION,
            f"Acúmulo de poeira em {energy.solar_dust_accumulation:.1%} — manutenção recomendada",
        )

    if energy.wind_blade_abrasion >= WIND_ABRASION_ALERT_THRESHOLD:
        enqueue_alert(
            state, AlertType.MAINTENANCE_REQUIRED,
            f"Abrasão das pás em {energy.wind_blade_abrasion:.1%} — manutenção recomendada",
        )

    # --- Compute generation ---
    energy.solar_generation_kw = compute_solar_generation_kw(
        solar_irradiance,
        energy.solar_dust_accumulation,
    )
    energy.wind_generation_kw = compute_wind_generation_kw(
        wind_speed,
        energy.wind_blade_abrasion,
    )

    # --- Consumption ---
    energy.total_consumption_kw = compute_total_consumption_kw(state.modules)

    # --- Battery ---
    energy.battery_reserve_kwh = update_battery(
        energy.battery_reserve_kwh,
        energy.balance_kw,
    )

    # --- History ---
    state.energy_history.append(energy.balance_kw)
    state.wind_history.append(wind_speed)
    state.dust_history.append(energy.solar_dust_accumulation)

