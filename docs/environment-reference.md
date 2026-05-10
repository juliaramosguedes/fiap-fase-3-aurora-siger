# Environment Reference — Aurora Siger

> Parâmetros ambientais marcianos usados na simulação.

---

## Temperatura

| Constante | Valor | Fonte |
|---|---|---|
| `MARS_EXTERNAL_TEMP_MIN_C` | −125 °C | NASA Mars Fact Sheet |
| `MARS_EXTERNAL_TEMP_MAX_C` | +20 °C | NASA Mars Fact Sheet |
| `COLONY_INTERNAL_TEMP_NOMINAL_C` | 21 °C | SIMULATED — conforto térmico humano padrão |
| `COLONY_INTERNAL_TEMP_MIN_C` | 18 °C | SIMULATED |
| `COLONY_INTERNAL_TEMP_MAX_C` | 26 °C | SIMULATED |

---

## Vento

| Constante | Valor | Fonte |
|---|---|---|
| `MARS_WIND_SPEED_MIN_MS` | 2,0 m/s | Viking Lander — Marspedia |
| `MARS_WIND_SPEED_MAX_MS` | 30,0 m/s | Viking Lander durante tempestades — Marspedia |
| `MARS_WIND_STORM_MIN_MS` | 17,0 m/s | Viking Lander — velocidade mínima de tempestade — Marspedia |

Durante tempestade, o vento é sorteado em `[17, 23,5]` m/s — metade inferior
do range de tempestade. Tempestades regionais costumam começar em velocidades
menores e escalar ao longo do evento.

---

## Tempestades de poeira

| Tipo | Duração | Velocidade | Referência |
|---|---|---|---|
| Local | < 3 sols = < 6 ciclos | 17–30 m/s | ScienceDirect (2022) |
| Regional | 3 sols a ~4 semanas = 6–56 ciclos | 17–30 m/s | ScienceDirect (2022); lovethenightsky.com |
| Global | Semanas a meses | 17–30 m/s | ScienceDirect (2024); NASA JSC (2018) |

O MGAB modela tempestades regionais (6–56 ciclos) como eventos padrão.
O modo `--stress` simula uma tempestade global com duração da simulação inteira.

**Efeito na geração solar:**
Irradiância reduzida: `irradiance × (1 - intensity × 0.85)`.
A 100% de intensidade, a solar cai 85% — baseado em observações do rover Opportunity
(NASA, 2018) durante a tempestade global de MY34.

**Efeito na geração eólica:**
Vento elevado → maior geração. É a complementaridade projetada entre solar e eólica.

**Acumulação de poeira:**
Taxa: `0,002 × (1 + intensity)` por ciclo durante a tempestade.
Manutenção solar bloqueada enquanto a tempestade está ativa.
Após a tempestade, manutenção retoma com probabilidade de 15% por ciclo diurno.

---

## Ciclo dia/noite

| Parâmetro | Valor | Fonte |
|---|---|---|
| `MARTIAN_DAY_HOURS` | 12,0 h | NASA Mars Fact Sheet |
| `MARTIAN_NIGHT_HOURS` | 12,6 h | NASA Mars Fact Sheet |

Um sol marciano ≈ 24,6h. Cada ciclo de simulação representa um meio-sol.
`is_daytime` alterna a cada ciclo, simulando o ciclo completo ao longo da execução.
