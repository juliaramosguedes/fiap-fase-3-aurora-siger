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
from .enums import AlertType, ModuleStatus, SystemStatus
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
    """Two-phase shed: essential modules → survival mode; non-essentials → full shutdown."""
    current_balance = state.energy.balance_kw
    changed = False

    # Phase 1 — essential modules (survival_consumption_kw set): reduce, never shut down
    for module in state.modules.values():
        if (module.status == ModuleStatus.OPERATIONAL
                and module.survival_consumption_kw is not None):
            reduction = module.current_consumption_kw - module.survival_consumption_kw
            module.status = ModuleStatus.SURVIVAL
            module.current_consumption_kw = module.survival_consumption_kw
            current_balance += reduction
            state.survival_stack.append(module.name)
            changed = True
            enqueue_alert(
                state, AlertType.ENERGY_DEFICIT,
                f"{module.name} em sobrevivência — consumo reduzido para {module.survival_consumption_kw:.1f} kW",
            )

    if current_balance >= 0:
        return changed

    # Phase 2 — non-essential modules (no survival_consumption_kw): full shutdown
    candidates = sorted(
        [m for m in state.modules.values()
         if m.status == ModuleStatus.OPERATIONAL and m.priority > 1
         and m.survival_consumption_kw is None],
        key=lambda m: m.priority,
        reverse=True,
    )

    for module in candidates:
        if current_balance >= 0:
            break
        module.status = ModuleStatus.SHUTDOWN
        state.shutdown_stack.append(module.name)
        current_balance += module.current_consumption_kw
        changed = True
        enqueue_alert(
            state, AlertType.ENERGY_DEFICIT,
            f"{module.name} desligado — bateria crítica: {state.energy.battery_reserve_kwh:.0f} kWh",
        )

    return changed


def restore_and_reactivate(state: ColonyState) -> bool:
    """Restore survival-mode and shutdown modules based on available generation margin.

    Processes most-critical modules first (lowest priority number).
    A module is only restored if the current generation margin covers its extra consumption.
    """
    generation = state.energy.solar_generation_kw + state.energy.wind_generation_kw
    available_margin = generation - state.energy.total_consumption_kw
    changed = False

    # Phase 1 — restore survival-mode modules (most critical first)
    for module_name in sorted(state.survival_stack, key=lambda n: state.modules[n].priority):
        module = state.modules[module_name]
        extra = module.nominal_consumption_kw - module.current_consumption_kw
        if available_margin >= extra:
            module.status = ModuleStatus.OPERATIONAL
            module.current_consumption_kw = module.nominal_consumption_kw
            available_margin -= extra
            state.survival_stack.remove(module_name)
            enqueue_alert(
                state, AlertType.ENERGY_DEFICIT,
                f"{module.name} restaurado — consumo normalizado: {module.nominal_consumption_kw:.0f} kW",
            )
            changed = True

    # Phase 2 — reactivate shutdown modules (most critical first)
    for module_name in sorted(state.shutdown_stack, key=lambda n: state.modules[n].priority):
        module = state.modules[module_name]
        cost = module.current_consumption_kw
        if available_margin >= cost:
            module.status = ModuleStatus.OPERATIONAL
            available_margin -= cost
            state.shutdown_stack.remove(module_name)
            enqueue_alert(
                state, AlertType.ENERGY_DEFICIT,
                f"{module.name} reativado — bateria recuperada: {state.energy.battery_reserve_kwh:.0f} kWh",
            )
            changed = True

    return changed


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
        restore_and_reactivate(state)
        still_recovering = bool(state.survival_stack or state.shutdown_stack)
        state.status = SystemStatus.RECOVERING if still_recovering else SystemStatus.OPERATIONAL

    else:
        state.status = SystemStatus.OPERATIONAL
