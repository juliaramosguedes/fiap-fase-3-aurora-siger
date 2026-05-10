# Energy Reference — Aurora Siger

> Fontes e justificativas para todas as constantes de energia do MGAB.
> Valores sem fonte publicada são marcados SIMULATED com justificativa.

---

## Localização da colônia

| Parâmetro | Valor | Fonte |
|---|---|---|
| Tipo de local | Top-3 sites de vento | Hartwick et al., Nature Astronomy (2023) |
| Critério | Potência eólica diurna média E33 > 24 kW em todos os momentos do ano | Hartwick et al. (2023), Fig. 5 |
| Justificativa | Seleção de local por recurso energético é a metodologia recomendada pelo paper | Hartwick et al. (2023) |

---

## Irradiância solar em Marte

| Constante | Valor | Fonte |
|---|---|---|
| `MARS_SOLAR_IRRADIANCE_WM2` | 590 W/m² | NASA TM-102299, Appelbaum & Flood (1989) |
| `MARS_SURFACE_IRRADIANCE_WM2` | 500 W/m² | SIMULATED — 590 menos ~15% absorção atmosférica |
| `SOLAR_PANEL_AREA_M2` | 1.000 m² | arXiv:2410.00066 — configuração base para 6 pessoas |
| `SOLAR_PANEL_EFFICIENCY` | 0,29 | SIMULATED — McMillon-Brown et al., ScienceDirect (2020) |
| `SOLAR_ARRAY_COUNT` | 1 | arXiv:2410.00066 — configuração de referência |

Geração nominal: `1000 × 500 × 0.29 / 1000 = 145 kW`

---

## Geração eólica — Enercon E33

| Constante | Valor | Fonte |
|---|---|---|
| `MARS_AIR_DENSITY_KGM3` | 0,017 kg/m³ | arXiv:2410.00066 |
| `WIND_TURBINE_DIAMETER_M` | 33,4 m | arXiv:2410.00066; Hartwick et al. (2023) — E33 |
| `WIND_TURBINE_RATED_POWER_EARTH_KW` | 330 kW | Especificação do fabricante Enercon |
| `WIND_TURBINE_EFFICIENCY` | 0,35 | SIMULATED — arXiv:2410.00066 usa curva Cp do fabricante escalada para Marte |
| `WIND_CUT_IN_MS` | 10,3 m/s | arXiv:2410.00066 |
| `WIND_CUT_OUT_MS` | 115,7 m/s | arXiv:2410.00066 |
| `WIND_AVERAGE_POWER_KW_BEST_SITES` | 24 kW/turbina | Hartwick et al., Nature Astronomy (2023) |
| `WIND_AVERAGE_POWER_KW_GENERAL` | 10 kW/turbina | Hartwick et al. (2023); citado em Interestingengineering (2023) |
| `WIND_TURBINE_COUNT` | 2 | 1 (arXiv:2410.00066) + 1 redundante (SIMULATED) |

**Por que o E33 gera ~10 kW em Marte (vs 330 kW na Terra):**
A densidade atmosférica de 0,017 kg/m³ é ~1,4% da terrestre. A fórmula `P ∝ ρ × v³` é linear em ρ.
Isso é confirmado por duas fontes independentes revisadas por pares (Hartwick 2023 e arXiv:2410.00066).
Não é erro de conversão — é física marciana confirmada.

**Por que escolhemos os melhores locais:**
Nos top-3 sites do Hartwick (2023), a potência diurna média sobe para 24 kW/turbina.
Selecionar o local da colônia com base em recurso energético é a abordagem científica recomendada.

**Vento noturno:**
NASA NTRS 19790057281 (Viking Lander 2): "in all seasons nighttime conditions are usually very quiet."
O E33 fica offline 70% das noites. A bateria cobre o déficit noturno.

---

## Bateria

| Constante | Valor | Fonte |
|---|---|---|
| `BATTERY_CAPACITY_KWH` | 312 kWh | arXiv:2410.00066 — capacidade por unidade |
| `BATTERY_COUNT` | 2 | 1 (arXiv:2410.00066) + 1 redundante (SIMULATED) |
| `BATTERY_MIN_PCT` | 20% | SIMULATED — margem de segurança operacional |

Capacidade total utilizável: `2 × 312 × 0.80 = 499 kWh`
Autonomia noturna (sem vento): `499 / 30 = 16,6h` — cobre noite de 12,6h com margem.

---

## Consumo da colônia

| Referência âncora | Valor | Fonte |
|---|---|---|
| Consumo total, 6 pessoas, 500 sols | 24–35 kW | Hartwick et al., Nature Astronomy (2023) |
| Consumo noturno implementado | 30 kW | Limite inferior do range — LSS+MED+HAB+PWR |
| Consumo diurno implementado | 46 kW | 30 kW + 16 kW módulos operacionais |

Distribuição por módulo: SIMULATED, proporcional por criticidade.
Sem fonte publicada para valores individuais por módulo em missão inicial.

---

## Degradação

| Constante | Valor | Fonte |
|---|---|---|
| `SOLAR_DUST_DEGRADATION_RATE_PER_CYCLE` | 0,002 | Lorenz et al., PSS (2021) — 0,2%/Sol |
| `SOLAR_DUST_CRITICAL_THRESHOLD` | 0,60 | InSight lander; ScienceDirect (2024) |
| `WIND_ABRASION_RATE_PER_CYCLE` | 0,001 | SIMULATED |

---

## Vento marciano — fontes reais

| Constante | Valor | Fonte |
|---|---|---|
| `MARS_WIND_SPEED_MIN_MS` | 2,0 m/s | NASA PDS Viking Met Data (VL1/VL2-M-MET-4-BINNED-P-T-V-V1.0) |
| `MARS_WIND_SPEED_MAX_MS` | 30,0 m/s | NASA PDS Viking Met Data — pico de tempestade |
| `MARS_WIND_STORM_MIN_MS` | 17,0 m/s | ScienceDirect, Perez-Prada et al. (2021) |
| `MARS_WIND_NIGHT_TYPICAL_MS` | 5,0 m/s | NASA NTRS 19790057281 — "nighttime conditions usually very quiet" |

**Nota sobre Marspedia:** fontes do tipo wiki comunitário (Marspedia) foram removidas do projeto.
Todos os valores de vento derivam agora de dados NASA (Viking Lander) e papers revisados por pares.
