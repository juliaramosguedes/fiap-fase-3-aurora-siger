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
    """Determine operational stage. CRITICAL triggers on battery depletion only — not on negative balance alone."""
    energy = state.energy

    if energy.battery_reserve_kwh <= BATTERY_MIN_KWH:
        return SystemStatus.CRITICAL

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

    if state.status == SystemStatus.RECOVERING:
        return SystemStatus.RECOVERING

    return SystemStatus.OPERATIONAL


def shutdown_to_stabilize(state: ColonyState) -> bool:
    """Shut down lowest-priority modules until balance >= 0 or no candidates remain."""
    candidates = sorted(
        [m for m in state.modules.values() if m.active and m.priority > 1],
        key=lambda m: m.priority,
        reverse=True,
    )

    if not candidates:
        return False

    current_balance = state.energy.balance_kw
    shutdown_count = 0

    for module in candidates:
        if current_balance >= 0:
            break
        module.active = False
        state.shutdown_stack.append(module.name)
        current_balance += module.current_consumption_kw
        shutdown_count += 1
        enqueue_alert(
            state, AlertType.ENERGY_DEFICIT,
            f"{module.name} desligado — bateria crítica: {state.energy.battery_reserve_kwh:.0f} kWh",
        )

    return shutdown_count > 0


def reactivate_one_module(state: ColonyState) -> bool:
    """Reactivate the most recently shut-down module (LIFO). Returns True if a module was reactivated."""
    if not state.shutdown_stack:
        return False

    module_name = state.shutdown_stack[-1]
    module = state.modules[module_name]
    module.active = True
    state.shutdown_stack.pop()
    enqueue_alert(
        state, AlertType.ENERGY_DEFICIT,
        f"{module.name} reativado — bateria recuperada: {state.energy.battery_reserve_kwh:.0f} kWh",
    )
    return True


def apply_maintenance(state: ColonyState) -> None:
    """Apply solar, wind, and equipment maintenance for the current cycle."""
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
    for module in state.modules.values():
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
    module = state.modules[module_name]
    increase = module.nominal_consumption_kw * EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT
    module.current_consumption_kw += increase
    enqueue_alert(
        state, AlertType.EQUIPMENT_FAILURE,
        f"{module.name} com falha — consumo aumentado para {module.current_consumption_kw:.0f} kW",
    )


def apply_anomaly_sensor_error(state: ColonyState, sensor: str) -> None:
    """Set a sensor field to None to simulate sensor failure."""
    if sensor == "wind":
        state.environment.wind_speed_ms = None
        enqueue_alert(state, AlertType.SENSOR_ERROR, "Sensor de vento offline")
    elif sensor == "solar":
        state.environment.solar_irradiance_wm2 = None
        enqueue_alert(state, AlertType.SENSOR_ERROR, "Sensor de irradiância solar offline")


def apply_decision(state: ColonyState) -> None:
    """Apply maintenance, determine stage, execute action, and update state.status."""
    apply_maintenance(state)

    new_status = determine_stage(state)

    if new_status == SystemStatus.CRITICAL:
        shutdown_to_stabilize(state)
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
