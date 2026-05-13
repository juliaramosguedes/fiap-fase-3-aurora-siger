from __future__ import annotations

from .constants import (
    BATTERY_MIN_KWH,
    BATTERY_TOTAL_CAPACITY_KWH,
    MARS_AIR_DENSITY_KGM3,
    MARTIAN_DAY_HOURS,
    MARTIAN_NIGHT_HOURS,
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


def compute_solar_generation_kw(
    solar_irradiance_wm2: float,
    solar_dust_accumulation: float,
) -> float:
    """P = AREA × irradiance × efficiency × (1 − dust) / 1000. Source: arXiv:2410.00066."""
    single_array_kw = (
        SOLAR_PANEL_AREA_M2
        * solar_irradiance_wm2
        * SOLAR_PANEL_EFFICIENCY
        * (1.0 - solar_dust_accumulation)
        / 1000.0
    )
    return single_array_kw * SOLAR_ARRAY_COUNT


def compute_wind_generation_kw(
    wind_speed_ms: float,
    wind_blade_abrasion: float,
) -> float:
    """P = ½ × ρ × A × v³ × η × (1 − abrasion) / 1000. Source: Betz (1926)."""
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


def accumulate_solar_dust(
    current_accumulation: float,
    dust_storm_intensity: float,
) -> float:
    """Base dust rate scaled by storm intensity, capped at 1.0. Source: Lorenz et al. (2021)."""
    increase = SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE * (1.0 + dust_storm_intensity)
    return min(1.0, current_accumulation + increase)


def accumulate_wind_abrasion(current_abrasion: float) -> float:
    """Constant abrasion rate per cycle, capped at 1.0. SIMULATED."""
    return min(1.0, current_abrasion + WIND_ABRASION_RATE_PER_CYCLE)


def perform_solar_maintenance() -> float:
    """Reset dust accumulation to zero. Simulates full panel cleaning by crew."""
    return 0.0


def perform_wind_maintenance() -> float:
    """Reset blade abrasion to zero. Simulates full blade servicing by crew."""
    return 0.0


def update_battery(
    battery_reserve_kwh: float,
    balance_kw: float,
    cycle_hours: float,
) -> float:
    """Charge or discharge the battery bank; clamped to [0, total capacity]."""
    updated = battery_reserve_kwh + balance_kw * cycle_hours
    return max(0.0, min(BATTERY_TOTAL_CAPACITY_KWH, updated))


def compute_total_consumption_kw(modules: dict) -> float:
    """Sum of current_consumption_kw across all active modules."""
    return sum(m.current_consumption_kw for m in modules.values() if m.active)


def update_energy_state(state: ColonyState) -> None:
    """Recompute the full energy state for the current cycle. Mutates state.energy in place."""
    env = state.environment
    energy = state.energy

    if env.wind_speed_ms is not None:
        wind_speed = env.wind_speed_ms
        state.last_valid_wind_speed_ms = wind_speed
    else:
        wind_speed = state.last_valid_wind_speed_ms
        enqueue_alert(
            state, AlertType.SENSOR_ERROR,
            "Sensor de velocidade do vento offline — usando última leitura válida",
        )

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
        solar_irradiance = 0.0  # night: no solar input regardless of sensor state

    energy.solar_dust_accumulation = accumulate_solar_dust(
        energy.solar_dust_accumulation,
        env.dust_storm_intensity,
    )
    energy.wind_blade_abrasion = accumulate_wind_abrasion(energy.wind_blade_abrasion)

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

    energy.solar_generation_kw = compute_solar_generation_kw(
        solar_irradiance,
        energy.solar_dust_accumulation,
    )
    energy.wind_generation_kw = compute_wind_generation_kw(
        wind_speed,
        energy.wind_blade_abrasion,
    )

    energy.total_consumption_kw = compute_total_consumption_kw(state.modules)

    cycle_hours = MARTIAN_DAY_HOURS if state.is_daytime else MARTIAN_NIGHT_HOURS
    energy.battery_reserve_kwh = update_battery(
        energy.battery_reserve_kwh,
        energy.balance_kw,
        cycle_hours,
    )

    state.energy_history.append(energy.balance_kw)
    state.wind_history.append(wind_speed)
    state.dust_history.append(energy.solar_dust_accumulation)
