"""
Decision logic for the MGAB — Autonomous Base Management Module.

Implements four operational stages. No day/night schedule — all modules
operate continuously. The E33 going offline at night (wind < cut-in) is
what creates nocturnal energy deficits; the battery covers them when possible.

Stage 0 — OPERATIONAL:
  balance_kw >= ENERGY_ALERT_THRESHOLD and no deteriorating trend.
  Battery charges automatically when balance > 0.

Stage 1 — ALERT (predictive):
  balance_kw >= ENERGY_ALERT_THRESHOLD BUT regression forecasts a crossing
  within FORECAST_HORIZON_CYCLES. No module is shut down — early warning only.

Stage 2 — CRITICAL (automatic action):
  battery <= BATTERY_MIN_KWH.
  Modules shut down in reverse priority order (8 -> 1). LSS-01 never shuts down.

Recovery — RECOVERING:
  battery > BATTERY_MIN_KWH after Stage 2.
  Modules reactivated one per cycle in reverse shutdown order (LIFO).

Night energy behavior (no schedule — purely physics-driven):
  E33 cut-in: 10.3 m/s. NASA NTRS 19790057281: nights usually quiet.
  70% of nights: E33 offline -> balance -46 kW -> battery drains 10.9h -> CRITICAL.
  30% of nights: E33 online -> balance -26 kW -> battery drains 19.2h -> OK.
  Daytime solar recharges battery the next morning.

Maintenance:
  Solar: blocked during active storm; probabilistic otherwise.
  Wind: probabilistic each cycle.
  Equipment failure: immediate for priority 1-3; probabilistic for others.
"""

from __future__ import annotations

import random

from .alerts import enqueue_alert
from .constants import (
    BATTERY_MIN_KWH,
    CRITICAL_MODULE_PRIORITY_THRESHOLD,
    ENERGY_ALERT_THRESHOLD_KW,
    ENERGY_CRITICAL_THRESHOLD_KW,
    EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT,
    EQUIPMENT_FAILURE_DEGRADATION_RATE,
    EQUIPMENT_FAILURE_MAX_CONSUMPTION_FACTOR,
    MAINTENANCE_PROBABILITY_PER_CYCLE,
    SOLAR_DUST_CRITICAL_THRESHOLD,
)
from .energy import perform_solar_maintenance, perform_wind_maintenance
from .enums import AlertType, SystemStatus
from .forecast import will_cross_threshold_soon
from .models import ColonyState, Module


def determine_stage(state: ColonyState) -> SystemStatus:
    """
    Determine the current operational stage.

    CRITICAL is triggered only by battery depletion — not by negative balance alone.
    Negative balance at night is expected and handled by the battery.
    ALERT is triggered by negative daytime balance or deteriorating forecast.
    Does not mutate state.
    """
    energy = state.energy

    # Battery depleted — CRITICAL regardless of time of day
    if energy.battery_reserve_kwh <= BATTERY_MIN_KWH:
        return SystemStatus.CRITICAL

    # Daytime: check balance threshold and forecast
    if state.is_daytime:
        if energy.balance_kw < ENERGY_CRITICAL_THRESHOLD_KW:
            return SystemStatus.CRITICAL

        if energy.balance_kw < ENERGY_ALERT_THRESHOLD_KW:
            return SystemStatus.ALERT

        if will_cross_threshold_soon(
            state.forecast.cycle_to_balance,
            current_cycle=state.cycle,
            threshold_kw=ENERGY_ALERT_THRESHOLD_KW,
        ):
            return SystemStatus.ALERT

    # Was recovering and still stable
    if state.status == SystemStatus.RECOVERING:
        return SystemStatus.RECOVERING

    return SystemStatus.OPERATIONAL


def shutdown_lowest_priority_module(state: ColonyState) -> bool:
    """
    Shut down the lowest-priority active module that is not LSS-01.

    Returns True if a module was shut down, False if none available.
    Tracks shutdown order in state.shutdown_stack for LIFO recovery.
    """
    candidates = [
        m for m in state.modules
        if m.active and m.priority > 1
    ]
    candidates.sort(key=lambda m: m.priority, reverse=True)

    if not candidates:
        return False

    target = candidates[0]
    target.active = False
    state.shutdown_stack.append(target.name)

    enqueue_alert(
        state, AlertType.ENERGY_DEFICIT,
        f"{target.name} desligado — bateria crítica: {state.energy.battery_reserve_kwh:.0f} kWh",
    )
    return True


def reactivate_one_module(state: ColonyState) -> bool:
    """
    Reactivate the most recently shut-down module (LIFO recovery).

    Returns True if a module was reactivated, False if stack is empty.
    """
    if not state.shutdown_stack:
        return False

    module_name = state.shutdown_stack[-1]
    for module in state.modules:
        if module.name == module_name:
            module.active = True
            state.shutdown_stack.pop()
            enqueue_alert(
                state, AlertType.ENERGY_DEFICIT,
                f"{module.name} reativado — bateria recuperada: {state.energy.battery_reserve_kwh:.0f} kWh",
            )
            return True

    return False


def apply_maintenance(state: ColonyState) -> None:
    """
    Apply maintenance actions for the current cycle.

    Solar: blocked during active storm (physically impossible to clean panels);
           automatic at critical threshold; probabilistic otherwise.
    Wind: probabilistic each cycle.
    Equipment failure: immediate for priority 1-3; probabilistic for others.
    """
    energy = state.energy

    # Solar panel cleaning — impossible during active dust storm
    if state.active_storm_cycles_remaining == 0:
        if energy.solar_dust_accumulation >= SOLAR_DUST_CRITICAL_THRESHOLD:
            energy.solar_dust_accumulation = perform_solar_maintenance()
            enqueue_alert(
                state, AlertType.MAINTENANCE_REQUIRED,
                "Limpeza emergencial dos painéis solares realizada",
            )
        elif random.random() < MAINTENANCE_PROBABILITY_PER_CYCLE:
            energy.solar_dust_accumulation = perform_solar_maintenance()

    # Wind blade servicing
    if random.random() < MAINTENANCE_PROBABILITY_PER_CYCLE:
        energy.wind_blade_abrasion = perform_wind_maintenance()

    # Equipment failure repair
    for module in state.modules:
        if module.current_consumption_kw > module.nominal_consumption_kw:
            is_critical = module.priority <= CRITICAL_MODULE_PRIORITY_THRESHOLD
            if is_critical or random.random() < MAINTENANCE_PROBABILITY_PER_CYCLE:
                module.current_consumption_kw = module.nominal_consumption_kw
                enqueue_alert(
                    state, AlertType.EQUIPMENT_FAILURE,
                    f"{module.name} reparado — consumo normalizado para {module.nominal_consumption_kw:.0f} kW",
                )
            else:
                increase = module.nominal_consumption_kw * EQUIPMENT_FAILURE_DEGRADATION_RATE
                module.current_consumption_kw = min(
                    module.nominal_consumption_kw * EQUIPMENT_FAILURE_MAX_CONSUMPTION_FACTOR,
                    module.current_consumption_kw + increase,
                )


def apply_anomaly_equipment_failure(state: ColonyState, module_name: str) -> None:
    """Increase consumption of a module due to equipment failure."""
    for module in state.modules:
        if module.name == module_name:
            increase = module.nominal_consumption_kw * EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT
            module.current_consumption_kw += increase
            enqueue_alert(
                state, AlertType.EQUIPMENT_FAILURE,
                f"{module.name} com falha — consumo aumentado para {module.current_consumption_kw:.0f} kW",
            )
            return


def apply_anomaly_sensor_error(state: ColonyState, sensor: str) -> None:
    """Set a sensor field to None to simulate sensor failure."""
    if sensor == "wind":
        state.environment.wind_speed_ms = None
        enqueue_alert(state, AlertType.SENSOR_ERROR, "Sensor de vento offline")
    elif sensor == "solar":
        state.environment.solar_irradiance_wm2 = None
        enqueue_alert(state, AlertType.SENSOR_ERROR, "Sensor de irradiância solar offline")


def apply_decision(state: ColonyState) -> None:
    """
    Apply the decision logic for the current cycle.

    Order:
    1. Apply maintenance
    2. Determine operational stage
    3. Act: shutdown (Critical) or reactivate (Recovering)
    4. Update state.status
    """
    apply_maintenance(state)

    new_status = determine_stage(state)

    if new_status == SystemStatus.CRITICAL:
        shutdown_lowest_priority_module(state)
        state.status = SystemStatus.CRITICAL

    elif new_status == SystemStatus.ALERT:
        if state.status != SystemStatus.ALERT:
            enqueue_alert(
                state, AlertType.PREDICTIVE_WARNING,
                f"Anomalia detectada. Balanço energético: {state.energy.balance_kw:.1f} kW",
            )
        state.status = SystemStatus.ALERT

    elif new_status == SystemStatus.RECOVERING or (
        state.status == SystemStatus.CRITICAL and new_status == SystemStatus.OPERATIONAL
    ):
        reactivated = reactivate_one_module(state)
        state.status = SystemStatus.RECOVERING if (reactivated and state.shutdown_stack) else SystemStatus.OPERATIONAL

    else:
        state.status = SystemStatus.OPERATIONAL
