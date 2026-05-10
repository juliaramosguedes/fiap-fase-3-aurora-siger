# Thresholds Reference — Aurora Siger

> Limiares de decisão do MGAB com justificativas.

---

## Limiares energéticos

| Constante | Valor | Estágio disparado | Justificativa |
|---|---|---|---|
| `ENERGY_ALERT_THRESHOLD_KW` | −20 kW | EM ALERTA | Balanço negativo moderado durante o dia; escalonado de −10 kW (base 193 kW) para −20 kW (base 253 kW) proporcionalmente |
| `ENERGY_CRITICAL_THRESHOLD_KW` | −60 kW | CRÍTICO | Balanço negativo severo durante o dia; escalonado de −30 kW para −60 kW proporcionalmente |
| `BATTERY_MIN_PCT` | 20% | CRÍTICO | Margem de segurança operacional; reserva para sistemas de emergência |

**Nota sobre limiares noturnos:**
À noite, `ENERGY_CRITICAL_THRESHOLD_KW` não é verificado contra `balance_kw`.
O déficit noturno de ~124 kW é esperado e planejado — coberto pelas baterias.
CRÍTICO à noite só dispara quando `battery_reserve_kwh ≤ BATTERY_MIN_KWH`.

---

## Limiares de previsão

| Constante | Valor | Uso |
|---|---|---|
| `FORECAST_MIN_CYCLES` | 4 | Mínimo de pontos para regressão confiável |
| `FORECAST_HORIZON_CYCLES` | 6 | Janela de previsão para alerta preditivo |

Com menos de 4 ciclos, qualquer previsão seria numericamente instável — a variância
do regressor é pequena demais para produzir slope confiável. 6 ciclos de horizonte
= 3 sols marcianos de antecedência para alerta.

---

## Limiares de manutenção

| Constante | Valor | Efeito |
|---|---|---|
| `SOLAR_DUST_ALERT_THRESHOLD` | 30% | Alerta de acúmulo |
| `SOLAR_DUST_CRITICAL_THRESHOLD` | 60% | Limpeza emergencial automática (se fora de tempestade) |
| `WIND_ABRASION_ALERT_THRESHOLD` | 25% | Alerta de abrasão |
| `MAINTENANCE_PROBABILITY_PER_CYCLE` | 15% | Probabilidade de manutenção por ciclo |
| `EQUIPMENT_FAILURE_CONSUMPTION_INCREASE_PCT` | 30% | Aumento de consumo por falha |
| `EQUIPMENT_FAILURE_DEGRADATION_RATE` | 5% | Aumento adicional por ciclo sem reparo |

**Limiar crítico de poeira (60%):**
Baseado no InSight lander, que perdeu potência progressivamente até encerrar operações
por acumulação sem limpeza (ScienceDirect, 2024). O valor de 60% representa o ponto
além do qual a degradação torna-se operacionalmente inaceitável.

---

## Limiares de duração de tempestade

| Constante | Valor | Fonte |
|---|---|---|
| `DUST_STORM_MIN_DURATION_CYCLES` | 6 | 3 sols × 2 ciclos/sol — mínimo para tempestade regional (ScienceDirect, 2022) |
| `DUST_STORM_MAX_DURATION_CYCLES` | 56 | ~4 semanas × 14 ciclos/semana — limite superior de tempestade regional |
