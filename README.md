# MGAB — Módulo de Gerenciamento Autônomo de Base

![Python](https://img.shields.io/badge/PYTHON-3.9+-3776AB?labelColor=0a0f1e&logo=python&logoColor=c5d8f0)
![Status](https://img.shields.io/badge/STATUS-OPERACIONAL-52be80?logo=startrek&labelColor=0a0f1e&logoColor=c5d8f0)
![Fase](https://img.shields.io/badge/FASE-3-c5d8f0?labelColor=0a0f1e&logoColor=c5d8f0)

> A Aurora Siger entrou em operação contínua.
> O desafio agora não é sobreviver — é manter a colônia funcionando de forma autônoma,
> estável e eficiente, sol após sol, mesmo quando Marte não coopera.

---

## O que é o MGAB

O MGAB é o sistema computacional integrado que gerencia a energia da colônia Aurora Siger.
A cada meio-sol marciano, ele calcula a geração solar e eólica, monitora o consumo de cada
módulo, prevê tendências de deterioração e toma decisões autônomas — desligando módulos
não-essenciais quando necessário e reativando-os assim que a situação melhora.

O sistema opera em quatro estágios: operacional, em alerta, crítico e recuperando.
Nenhuma intervenção humana é necessária para transitar entre eles.

---

## A colônia

Aurora Siger opera com uma tripulação de 6 pessoas, dimensionada segundo a NASA DRA 5.0
(Drake, 2009) e o estudo de energia marciana de Hartwick et al. (Nature Astronomy, 2023).

| # | Papel | Módulo primário |
|---|---|---|
| 1 | Commander | COM-01 Communications |
| 2 | Pilot | LOG-01 Logistics |
| 3 | Medical Officer | MED-01 Medical |
| 4 | Scientist | SCI-01 Science Lab |
| 5 | Engineer ECLSS | LSS-01 Life Support + HAB-01 Habitat |
| 6 | Engineer Power/ISRU | PWR-01 Power Systems + MIN-01 ISRU Mining |

6 é o mínimo seguro: garante um substituto treinado para cada expertise crítica.
Módulos críticos têm pessoa dedicada; nenhum módulo que pode matar é compartilhado.

### Módulos e prioridades

Todos os módulos operam 24h de forma autônoma. A literatura confirma: "life support
systems were controlled automatically" (CELSS, NIH 2019). Desligamentos são
exclusivamente por decisão energética — nunca por horário.

| Módulo | Prioridade | Consumo nominal |
|---|---|---|
| LSS-01 Life Support | 1 — nunca desliga | 14 kW |
| MED-01 Medical | 2 — essencial | 5 kW |
| HAB-01 Habitat | 3 — essencial | 7 kW |
| PWR-01 Power Systems | 4 — essencial | 4 kW |
| COM-01 Communications | 5 — operacional | 3 kW |
| SCI-01 Science Lab | 6 — operacional | 5 kW |
| LOG-01 Logistics | 7 — operacional | 3 kW |
| MIN-01 ISRU Mining | 8 — desliga primeiro | 5 kW |

**Consumo total: 46 kW** — dentro do range de 24–35 kW para sistemas críticos + 16 kW
de módulos operacionais. Fonte âncora: Hartwick et al. (2023), 24–35 kW para 6 pessoas.

---

## Infraestrutura energética

### Por que solar e eólica juntas?

Durante tempestades de areia, a geração solar cai até 85%. Quando o vento está forte,
as turbinas compensam. Quando o vento está fraco (noites calmas), a bateria cobre.
A combinação das três fontes é a arquitetura descrita por Hartwick et al. (2023).

### Localização

Aurora Siger está situada em um dos três melhores locais de geração eólica de Marte,
identificados por Hartwick et al. (Nature Astronomy, 2023). Nesses locais, a potência
eólica diurna média do E33 excede 24 kW em todos os momentos do ano simulado.

Selecionar o local com base em recurso energético é a metodologia recomendada pelo paper.

### Configuração instalada

| Componente | Quantidade | Especificação | Fonte |
|---|---|---|---|
| Painel solar | 1 × 1.000 m² | 29% eficiência | arXiv:2410.00066 |
| Turbinas eólicas | 2 × E33 (33,4 m) | ~24 kW nos melhores locais | Hartwick et al. (2023) |
| Baterias | 2 × 312 kWh | 80% DoD operacional | arXiv:2410.00066 |

A segunda turbina e a segunda bateria são redundância operacional — tolerância a falha simples.

### Balanço energético

| Período | Geração | Consumo | Balanço |
|---|---|---|---|
| Dia (nominal) | 145 kW solar + 48 kW eólica | 46 kW | +147 kW |
| Noite com vento | 0 + 20 kW eólica | 46 kW | −26 kW → 19,2h autonomia |
| Noite sem vento (70%) | 0 + 0 kW | 46 kW | −46 kW → 10,9h → **CRÍTICO** |
| Tempestade + vento | 22 kW solar + 48 kW | 46 kW | +24 kW — sistema aguenta |
| Tempestade + sem vento | 22 kW solar + 0 kW | 46 kW | −24 kW → CRÍTICO em ~20h |

---

## Como funciona

A cada ciclo (meio-sol marciano ≈ 12h):

```
1. Avança o ciclo (dia ↔ noite)
2. Atualiza o ambiente (variação ou tempestade persistente)
3. Injeta anomalia (se configurado)
4. Calcula geração solar e eólica
5. Calcula consumo total (46 kW — todos os módulos ativos)
6. Atualiza bateria (carga ou descarga)
7. Atualiza regressões lineares (Welford incremental)
8. Determina estágio operacional
9. Executa ação (desliga módulo ou reativa)
10. Exibe relatório do ciclo
```

### Regressão linear para previsão

Duas regressões (Welford, O(1) por atualização):
- `vento → geração eólica`: relação física
- `ciclo → balanço energético`: tendência operacional

Quando a tendência prevê cruzamento do limiar de alerta nos próximos 6 ciclos,
o sistema emite alerta preditivo antes de qualquer falha real.

---

## Como executar

```bash
python main.py                              # cenário padrão, 48 ciclos
python main.py --cycles 96                 # número de ciclos customizado
python main.py --random                    # cenário aleatório
python main.py --anomaly 0.3               # 30% de chance de anomalia por ciclo
python main.py --random --anomaly 0.4      # aleatório com anomalias frequentes
python main.py --stress                    # tempestade global forçada, 200 ciclos
python main.py --stress --cycles 400       # tempestade global longa
python main.py --seed 42                   # semente para reprodutibilidade
```

> [!CAUTION]
> Em `--stress`, uma tempestade global envolve a colônia desde o ciclo 1.
> Noites sem vento drenam a bateria antes do amanhecer.
> Resistência é inútil.

> [!IMPORTANT]
> O projeto não usa bibliotecas externas. Apenas Python 3.9+ padrão.
> Nenhuma instalação adicional necessária.

---

## Exemplo de saída

```
=================================================================
☄️ CICLO 103 [NOITE] — AURORA SIGER  [CRÍTICO]
   Resistência é inútil. Protocolo de emergência ativado.
=================================================================
🛰  Ambiente
   Vento: 5.2 m/s              Irradiância: NOITE
⚡  Energia
   Geração: solar     0.0 kW  |  eólica     0.0 kW
   Consumo:    46.0 kW  |  Balanço:    -46.0 kW
   Bateria:   124.8 kWh (20.0%)  |  Poeira: 12.4%  Abrasão: 1.1%
🛰  Módulos ativos (7/8): LSS-01, MED-01, HAB-01, PWR-01, COM-01, SCI-01, LOG-01
   Inativos: MIN-01 ISRU Mining
🌙  Alertas (1):
   [DÉFICIT ENERGÉTICO] MIN-01 ISRU Mining desligado — bateria crítica: 124 kWh
```

---

## Critérios da atividade atendidos

| Critério | Implementação |
|---|---|
| Estruturação de dados | `ColonyState` hierárquico, `deque` para alertas FIFO, dicionários de enumeração |
| Lógica de decisão | 4 estágios com condições explícitas, desligamento por prioridade, recuperação LIFO |
| Modelagem e previsão | Fórmulas físicas reais (Betz, solar); regressão Welford com previsão de limiar |
| Implementação Python | Funções puras, separação por módulo, sem bibliotecas externas |
| Documentação | README, ENGINEERING_GUIDE, `docs/`, constantes com fonte inline |

---

🧑‍🚀 Julia Ramos | RM568988 | FIAP — Ciência da Computação
