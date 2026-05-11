"""
Report module for the MGAB — Autonomous Base Management Module.

Handles all terminal output. No logic lives here — only formatting.

Emoji map (from GUIA_ESTILO_AURORA_SIGER.md — fixed palette):
  🛰  colony state / sensors
  ⚡  energy generation and balance
  ☄️  decision logic / critical
  📡  forecast / regression
  🌙  alert queue / maintenance
  🖖  final report (used once, at the end)

Status badges map directly to SystemStatus enum values.
Frases de sucesso/falha from GUIA_ESTILO_AURORA_SIGER.md.
"""

from __future__ import annotations

from collections import deque

from .constants import BATTERY_TOTAL_CAPACITY_KWH, FORECAST_MIN_CYCLES, SEPARATOR
from .enums import SystemStatus
from .forecast import is_regression_reliable
from .models import ColonyState


# ---------------------------------------------------------------------------
# Status phrases (GUIA_ESTILO_AURORA_SIGER.md)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Cycle report
# ---------------------------------------------------------------------------


def display_cycle_report(state: ColonyState) -> None:
    """Print a concise report for the current simulation cycle."""
    period = "DIA" if state.is_daytime else "NOITE"
    status_emoji = STATUS_EMOJI[state.status]
    status_phrase = STATUS_PHRASES[state.status]

    print(SEPARATOR)
    print(f"{status_emoji} CICLO {state.cycle:>3} [{period}] — AURORA SIGER  [{state.status.value}]")
    print(f"   {status_phrase}")
    print(SEPARATOR)

    # Environment
    wind = state.environment.wind_speed_ms
    irr = state.environment.solar_irradiance_wm2
    dust_int = state.environment.dust_storm_intensity
    wind_str = f"{wind:.1f} m/s" if wind is not None else "SENSOR OFFLINE"
    irr_str = f"{irr:.0f} W/m²" if irr is not None else ("NOITE" if not state.is_daytime else "SENSOR OFFLINE")

    print(f"🛰  Ambiente")
    print(f"   Vento: {wind_str:<20} Irradiância: {irr_str}")
    if dust_int > 0:
        print(f"   ⚠  Tempestade de poeira — intensidade: {dust_int:.0%}")

    # Energy
    energy = state.energy
    battery_pct = energy.battery_reserve_kwh / BATTERY_TOTAL_CAPACITY_KWH * 100
    print(f"⚡  Energia")
    print(f"   Geração: solar {energy.solar_generation_kw:>7.1f} kW  |  eólica {energy.wind_generation_kw:>7.1f} kW")
    print(f"   Consumo: {energy.total_consumption_kw:>7.1f} kW  |  Balanço: {energy.balance_kw:>+8.1f} kW")
    print(f"   Bateria: {energy.battery_reserve_kwh:>7.1f} kWh ({battery_pct:.1f}%)  |  "
          f"Poeira: {energy.solar_dust_accumulation:.1%}  Abrasão: {energy.wind_blade_abrasion:.1%}")

    # Active modules
    active_names = [m.name for m in state.modules if m.active]
    inactive_names = [m.name for m in state.modules if not m.active]
    print(f"🛰  Módulos ativos ({len(active_names)}/8): {', '.join(active_names)}")
    if inactive_names:
        print(f"   Inativos: {', '.join(inactive_names)}")

    # Forecast
    regression = state.forecast.cycle_to_balance
    if is_regression_reliable(regression):
        slope = regression.slope
        direction = "↓ deteriorando" if slope is not None and slope < -1 else "→ estável"
        predicted = regression.predict(float(state.cycle + 6))
        predicted_str = f"{predicted:+.1f} kW" if predicted is not None else "N/A"
        print(f"📡  Previsão (+6 ciclos): {predicted_str}  [{direction}]")
    else:
        remaining = FORECAST_MIN_CYCLES - regression.count
        print(f"📡  Previsão: aguardando {remaining} ciclo(s) para ativar regressão")

    # Alerts
    alerts = list(state.alert_queue)
    current_cycle_alerts = [a for a in alerts if a["cycle"] == state.cycle]
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

    cycles_run = state.cycle
    battery_pct = state.energy.battery_reserve_kwh / BATTERY_TOTAL_CAPACITY_KWH * 100

    print(f"🛰  Ciclos simulados: {cycles_run}")
    print(f"   Status final: {state.status.value}")
    print(f"   Bateria final: {state.energy.battery_reserve_kwh:.1f} kWh ({battery_pct:.1f}%)")
    print(f"   Poeira acumulada: {state.energy.solar_dust_accumulation:.1%}")
    print(f"   Abrasão das pás: {state.energy.wind_blade_abrasion:.1%}")

    if state.energy_history:
        avg_balance = sum(state.energy_history) / len(state.energy_history)
        min_balance = min(state.energy_history)
        max_balance = max(state.energy_history)
        print(f"⚡  Balanço energético")
        print(f"   Médio: {avg_balance:+.1f} kW  |  Mínimo: {min_balance:+.1f} kW  |  Máximo: {max_balance:+.1f} kW")

    total_alerts = len(state.alert_queue)
    print(f"🌙  Total de alertas: {total_alerts}")

    active_count = sum(1 for m in state.modules if m.active)
    print(f"🛰  Módulos ativos ao final: {active_count}/8")

    regression = state.forecast.cycle_to_balance
    if is_regression_reliable(regression) and regression.slope is not None:
        trend = "deterioração" if regression.slope < 0 else "melhora"
        print(f"📡  Tendência final: {trend} ({regression.slope:+.2f} kW/ciclo)")

    print(SEPARATOR)
