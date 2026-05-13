from __future__ import annotations

from .constants import BATTERY_MIN_KWH, BATTERY_TOTAL_CAPACITY_KWH, FORECAST_MIN_CYCLES, SEPARATOR
from .enums import SystemStatus
from .forecast import is_regression_reliable
from .models import ColonyState


_BAR_WIDTH      = 20
_SOLAR_MAX_KW   = 145.0
_WIND_MAX_KW    = 50.0
_CONSUME_MAX_KW = 46.0


STATUS_PHRASES = {
    SystemStatus.OPERATIONAL: "Sistemas nominais. Missão em curso.",
    SystemStatus.ALERT:       "Anomalia detectada. Monitoramento intensificado.",
    SystemStatus.CRITICAL:    "Resistência é inútil. Protocolo de emergência ativado.",
    SystemStatus.RECOVERING:  "Sistemas restaurados. Retomando operação nominal.",
}

FINAL_PHRASES = {
    SystemStatus.OPERATIONAL: "Vida longa e próspera. 🖖",
    SystemStatus.RECOVERING:  "A colônia resiste. Recuperação em andamento.",
    SystemStatus.ALERT:       "Anomalia persistente ao encerrar. Monitoramento contínuo recomendado.",
    SystemStatus.CRITICAL:    "Resistência é inútil. Missão encerrada em estado crítico.",
}

STATUS_EMOJI = {
    SystemStatus.OPERATIONAL: "⚡",
    SystemStatus.ALERT:       "☄️",
    SystemStatus.CRITICAL:    "☄️",
    SystemStatus.RECOVERING:  "⚡",
}


def _bar(value: float, max_value: float) -> str:
    ratio  = min(1.0, max(0.0, value / max_value)) if max_value > 0 else 0.0
    filled = round(ratio * _BAR_WIDTH)
    return "█" * filled + "░" * (_BAR_WIDTH - filled)


def _battery_status(reserve_kwh: float, pct: float) -> str:
    return next(
        (tag for met, tag in [
            (reserve_kwh <= BATTERY_MIN_KWH, "CRÍTICO"),
            (pct < 30, "ALERTA"),
        ] if met),
        "OK",
    )


# ---------------------------------------------------------------------------
# Cycle report
# ---------------------------------------------------------------------------


def display_cycle_report(state: ColonyState) -> None:
    """Print a concise report for the current simulation cycle."""
    period = "DIA" if state.is_daytime else "NOITE"

    print(SEPARATOR)
    print(f"{STATUS_EMOJI[state.status]} CICLO {state.cycle:>3} [{period}] — AURORA SIGER  [{state.status.value}]")
    print(f"   {STATUS_PHRASES[state.status]}")
    print(SEPARATOR)

    wind     = state.environment.wind_speed_ms
    irr      = state.environment.solar_irradiance_wm2
    wind_str = f"{wind:.1f} m/s" if wind is not None else "SENSOR OFFLINE"
    irr_str  = f"{irr:.0f} W/m²" if irr is not None else ("NOITE" if not state.is_daytime else "SENSOR OFFLINE")

    print(f"🛰  Ambiente")
    print(f"   Vento: {wind_str:<20} Irradiância: {irr_str}")
    if state.environment.dust_storm_intensity > 0:
        print(f"   ⚠  Tempestade de poeira — intensidade: {state.environment.dust_storm_intensity:.0%}")

    energy      = state.energy
    battery_pct = energy.battery_reserve_kwh / BATTERY_TOTAL_CAPACITY_KWH * 100

    print(f"⚡  Energia")
    print(f"   {'Bateria':<8} [{_bar(energy.battery_reserve_kwh, BATTERY_TOTAL_CAPACITY_KWH)}]  {energy.battery_reserve_kwh:>7.1f} kWh  {battery_pct:>5.1f}%  ({_battery_status(energy.battery_reserve_kwh, battery_pct)})")
    print(f"   {'Solar':<8} [{_bar(energy.solar_generation_kw,    _SOLAR_MAX_KW)}]  {energy.solar_generation_kw:>7.1f} kW")
    print(f"   {'Eólica':<8} [{_bar(energy.wind_generation_kw,     _WIND_MAX_KW)}]  {energy.wind_generation_kw:>7.1f} kW")
    print(f"   {'Consumo':<8} [{_bar(energy.total_consumption_kw,   _CONSUME_MAX_KW)}]  {energy.total_consumption_kw:>7.1f} kW  |  Balanço: {energy.balance_kw:>+8.1f} kW")
    print(f"   {'Poeira':<8} [{_bar(energy.solar_dust_accumulation, 1.0)}]  {energy.solar_dust_accumulation:>6.1%}")
    print(f"   {'Abrasão':<8} [{_bar(energy.wind_blade_abrasion,    1.0)}]  {energy.wind_blade_abrasion:>6.1%}")

    active_names   = [m.name for m in state.modules.values() if m.active]
    inactive_names = [m.name for m in state.modules.values() if not m.active]
    print(f"🛰  Módulos ativos ({len(active_names)}/8): {', '.join(active_names)}")
    if inactive_names:
        print(f"   Inativos: {', '.join(inactive_names)}")

    regression = state.forecast.cycle_to_balance
    if is_regression_reliable(regression):
        slope         = regression.slope
        direction     = "↓ deteriorando" if slope is not None and slope < -1 else "→ estável"
        predicted     = regression.predict(float(state.cycle + 6))
        predicted_str = f"{predicted:+.1f} kW" if predicted is not None else "N/A"
        print(f"📡  Previsão (+6 ciclos): {predicted_str}  [{direction}]")
    else:
        remaining = FORECAST_MIN_CYCLES - regression.count
        print(f"📡  Previsão: aguardando {remaining} ciclo(s) para ativar regressão")

    wind_reg = state.forecast.wind_to_generation
    if is_regression_reliable(wind_reg):
        wind_input    = state.last_valid_wind_speed_ms
        wind_pred     = wind_reg.predict(wind_input)
        wind_pred_str = f"{wind_pred:.1f} kW" if wind_pred is not None else "N/A"
        print(f"🌬  Eólica prevista (regressão): {wind_pred_str}  @ {wind_input:.1f} m/s")

    solar_reg = state.forecast.cycle_to_solar
    if is_regression_reliable(solar_reg):
        solar_pred     = solar_reg.predict(float(state.cycle + 6))
        solar_pred_str = f"{solar_pred:.1f} kW" if solar_pred is not None else "N/A"
        print(f"☀️   Solar prevista (+6 ciclos): {solar_pred_str}")

    current_cycle_alerts = [a for a in state.alert_queue if a["cycle"] == state.cycle]
    if current_cycle_alerts:
        print(f"🌙  Alertas ({len(current_cycle_alerts)}):")
        for alert in current_cycle_alerts:
            print(f"   [{alert['type'].value}] {alert['detail']}")


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------


def display_final_report(state: ColonyState) -> None:
    """Print the summary report at the end of the simulation."""
    print()
    print(SEPARATOR)
    print(f"🖖  RELATÓRIO FINAL — AURORA SIGER")
    print(f"   {FINAL_PHRASES[state.status]}")
    print(SEPARATOR)

    battery_pct = state.energy.battery_reserve_kwh / BATTERY_TOTAL_CAPACITY_KWH * 100

    print(f"🛰  Ciclos simulados: {state.cycle}")
    print(f"   Status final: {state.status.value}")
    print(f"   {'Bateria':<8} [{_bar(state.energy.battery_reserve_kwh, BATTERY_TOTAL_CAPACITY_KWH)}]  {state.energy.battery_reserve_kwh:>7.1f} kWh  {battery_pct:>5.1f}%  ({_battery_status(state.energy.battery_reserve_kwh, battery_pct)})")
    print(f"   {'Poeira':<8} [{_bar(state.energy.solar_dust_accumulation, 1.0)}]  {state.energy.solar_dust_accumulation:>6.1%}")
    print(f"   {'Abrasão':<8} [{_bar(state.energy.wind_blade_abrasion,    1.0)}]  {state.energy.wind_blade_abrasion:>6.1%}")

    if state.energy_history:
        avg_balance = sum(state.energy_history) / len(state.energy_history)
        min_balance = min(state.energy_history)
        max_balance = max(state.energy_history)
        print(f"⚡  Balanço energético")
        print(f"   Médio: {avg_balance:+.1f} kW  |  Mínimo: {min_balance:+.1f} kW  |  Máximo: {max_balance:+.1f} kW")

    print(f"🌙  Total de alertas: {len(state.alert_queue)}")
    print(f"🛰  Módulos ativos ao final: {sum(1 for m in state.modules.values() if m.active)}/8")

    regression = state.forecast.cycle_to_balance
    if is_regression_reliable(regression) and regression.slope is not None:
        trend = "deterioração" if regression.slope < 0 else "melhora"
        print(f"📡  Tendência final: {trend} ({regression.slope:+.2f} kW/ciclo)")

    print(SEPARATOR)
