# ENGINEERING GUIDE — MGAB
## Módulo de Gerenciamento Autônomo de Base · Aurora Siger · FIAP

> Walkthrough técnico do código para engenheiros.
> Cobre decisões de arquitetura, estruturas de dados, algoritmos e modelos matemáticos.

---

## Estrutura do projeto

```
fiap-fase-3-aurora-siger/
├── src/
│   ├── constants.py     — única fonte de verdade para todas as constantes
│   ├── enums.py         — enumerações do domínio
│   ├── models.py        — dataclasses de estado + AlertEntry TypedDict
│   ├── alerts.py        — enqueue_alert (fila de alertas tipada)
│   ├── scenarios.py     — inicialização do ColonyState
│   ├── energy.py        — cálculo de geração, consumo e bateria
│   ├── forecast.py      — regressão linear online (Welford)
│   ├── decision.py      — lógica de decisão em quatro estágios
│   ├── simulation.py    — loop principal e injeção de anomalias
│   └── report.py        — output formatado
├── docs/                — referências técnicas por domínio
└── main.py              — entry point com CLI
```

**Separação de responsabilidades:**
- `energy.py` calcula — nunca decide
- `decision.py` decide — nunca calcula geração
- `report.py` formata — nunca contém lógica
- `constants.py` define — nunca importa de outros módulos do projeto

---

## Estruturas de dados

### ColonyState

```python
@dataclass
class ColonyState:
    cycle: int
    is_daytime: bool                      # controla geração solar (não schedule de módulos)
    environment: EnvironmentReading
    energy: EnergyState
    modules: list[Module]
    forecast: ForecastState
    status: SystemStatus
    energy_history: list[float]
    wind_history: list[float]
    dust_history: list[float]
    alert_queue: deque[AlertEntry]        # FIFO — alertas em ordem de chegada
    active_storm_cycles_remaining: int   # > 0 = tempestade ativa
    last_valid_solar_irradiance_wm2: float
    last_valid_wind_speed_ms: float
    shutdown_stack: list[str]            # LIFO — ordem inversa para recovery
```

`is_daytime` controla exclusivamente a geração solar (solar = 0 à noite).
Não é usado para ligar/desligar módulos — todos os módulos operam 24h.
Fonte: CELSS (NIH, 2019): "life support systems were controlled automatically";
NASA ECLSS (NTRS 20230002103): "automation to reduce regular maintenance time".

`shutdown_stack` é uma pilha LIFO declarada em `ColonyState`. Cada desligamento
empilha o nome do módulo; cada ciclo de recovery desempilha e reativa o topo.

### EnergyState

```python
@property
def balance_kw(self) -> float:
    return self.solar_generation_kw + self.wind_generation_kw - self.total_consumption_kw
```

`balance_kw` é a única métrica que dispara decisões. Sempre recalculada.

### OnlineRegression (Welford)

```python
@dataclass
class OnlineRegression:
    count: int
    mean_independent: float
    mean_dependent: float
    variance_independent: float   # Σ(x - x̄)² acumulado
    covariance: float             # Σ(x - x̄)(y - ȳ) acumulado
```

O(1) por atualização, O(1) memória. Sem histórico armazenado.

---

## Modelagem matemática

### Geração solar

```
P_solar = AREA × irradiance × EFFICIENCY × (1 - dust) / 1000 × ARRAY_COUNT
```

- `AREA = 1000 m²`, `EFFICIENCY = 0.29`, `ARRAY_COUNT = 1`
- `/1000` converte W → kW
- Nominal: `1000 × 500 × 0.29 / 1000 = 145 kW`
- À noite: `irradiance = 0.0` → solar = 0 kW

### Geração eólica (Enercon E33)

```
P_eolica = 0.5 × ρ × A × v³ × η × (1 - abrasion) / 1000 × TURBINE_COUNT
```

- `ρ = 0.017 kg/m³`, `A = π × (33.4/2)² = 876.2 m²`, `η = 0.35`
- `TURBINE_COUNT = 2`
- Fora de `[10.3, 115.7]` m/s: retorna 0 kW
- Nos melhores locais (Hartwick 2023): ~24 kW/turbina média diurna
- Média planetária: ~10 kW/turbina (Hartwick 2023)
- **Noites: 70% das vezes vento < cut-in → E33 offline**

### Por que o E33 gera 10 kW em Marte (vs 330 kW na Terra):

A fórmula é `P ∝ ρ × v³`. Com `ρ_Marte = 0.017 kg/m³` vs `ρ_Terra = 1.225 kg/m³`,
a razão é 1.4%. Confirmado por Hartwick et al. (2023) e arXiv:2410.00066.
Não é erro — é física marciana.

### Regressão linear online (Welford)

```
count += 1
δ = x - mean_x
mean_x += δ / count
mean_y += (y - mean_y) / count
variance_x += δ × (x - mean_x)   # pós-atualização
covariance  += δ × (y - mean_y)  # pós-atualização

slope     = covariance / variance_x
intercept = mean_y - slope × mean_x
```

Duas regressões em `ForecastState`:
1. `wind_to_generation`: vento → geração eólica (relação física)
2. `cycle_to_balance`: ciclo → balanço energético (tendência operacional)

---

## Lógica de decisão

### Por que não há schedule dia/noite de módulos

Todos os módulos operam 24h. A literatura confirma:
- CELSS (NIH 2019): life support autônomo
- NASA ECLSS (NTRS 20230002103): automação reduz demanda de atenção da tripulação
- Space S&T (2021): ISRU pode operar 24h ou 8h — decisão de energia, não de pessoas

O déficit noturno é físico: solar = 0, E33 offline 70% das noites. A bateria cobre
o déficit; quando esgota, o sistema entra em CRÍTICO.

### Quatro estágios

| Estágio | Condição | Ação |
|---|---|---|
| OPERACIONAL | `battery > MIN` e sem tendência ruim (dia) | Carrega bateria se `balance > 0` |
| EM ALERTA | `battery > MIN` e regressão prevê cruzamento em ≤ 6 ciclos (dia) | Apenas alerta |
| CRÍTICO | `battery ≤ BATTERY_MIN_KWH` | Desliga módulo de menor prioridade |
| RECUPERANDO | `battery > BATTERY_MIN_KWH` após CRÍTICO | Reativa 1 módulo por ciclo (LIFO) |

**CRÍTICO só dispara por bateria depleta** — balanço negativo noturno é esperado.

### Modelo de tempestade

Duração sorteada: `random.randint(6, 56)` ciclos (regional).
Durante tempestade:
- Solar reduzida: `irradiance × (1 - intensity × 0.85)`
- Dia: vento elevado `[17, 21]` m/s
- Noite: 60% chance abaixo do cut-in (NASA NTRS 19790057281)
- Manutenção solar bloqueada

---

## Decisões técnicas relevantes

**Consumo constante 46 kW:** baseado em Hartwick et al. (2023) — 24-35 kW para missão
de 6 pessoas + 16 kW de módulos operacionais (COM, SCI, LOG, MIN). Sem schedule noturno.

**1 painel + 2 turbinas + 2 baterias:** configuração de referência do arXiv:2410.00066
mais 1 unidade redundante de cada (SIMULATED). Single-failure tolerance.

**Localização nos top-3 sites do Hartwick (2023):** única forma honesta de justificar
24 kW/turbina como média diurna. Seleção por recurso energético é a metodologia
recomendada pelo paper.

**Marspedia removida:** wiki comunitário sem revisão por pares. Todos os valores
substituídos por NASA PDS, Nature Astronomy, arXiv revisado.
