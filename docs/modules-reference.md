# Modules Reference — Aurora Siger

> Consumo nominal, justificativas e papéis de tripulação para cada módulo.

---

## Consumo total da colônia

| Período | Módulos ativos | Consumo total |
|---|---|---|
| Dia | Todos (8) | 253 kW |
| Noite | LSS, MED, HAB, PWR (4) | 175 kW |

---

## Módulos individuais

### LSS-01 Life Support — 132 kW
**Responsável:** Engineer ECLSS (Engineer 1)
**Prioridade:** 1 — nunca desliga por lógica de energia
**Período:** 24h

132 kW = 22 kW/pessoa × 6 pessoas.
A Marspedia cita ~60 kW/pessoa para colônia autossuficiente completa (com agricultura,
produção de água em escala, etc.). 22 kW/pessoa representa suporte de vida básico
automatizado de missão inicial: ar, pressão, temperatura e reciclagem de água.

Fonte: SIMULATED — derivado de Marspedia com escalonamento para missão inicial.

---

### MED-01 Medical — 15 kW
**Responsável:** Medical Officer
**Prioridade:** 2 — essencial
**Período:** 24h

Infraestrutura médica fixa: equipamentos de monitoramento contínuo, sistemas de
emergência, suprimentos refrigerados. Sem fonte direta para módulo médico isolado
em Marte — valor SIMULATED por analogia com unidade médica remota.

---

### HAB-01 Habitat — 18 kW
**Responsável:** Engineer ECLSS (compartilha infraestrutura com LSS-01)
**Prioridade:** 3 — essencial
**Período:** 24h

18 kW = 3 kW/pessoa × 6 pessoas.
Fonte: arXiv:2410.00066 — habitat consome 13–23 kW para 6 pessoas; valor central
dividido por pessoa e multiplicado pela tripulação.

LSS-01 e HAB-01 compartilham o mesmo engenheiro porque operam sobre a mesma
infraestrutura física de pressurização, temperatura e HVAC.

---

### PWR-01 Power Systems — 10 kW
**Responsável:** Engineer Power/ISRU (Engineer 2)
**Prioridade:** 4 — essencial
**Período:** 24h

Distribuição elétrica, inversores, conversores, controle de carga. Falha neste módulo
afeta todos os outros. Valor SIMULATED — sem referência direta para infraestrutura
de distribuição isolada em base marciana.

---

### COM-01 Communications — 8 kW
**Responsável:** Commander (papel secundário)
**Prioridade:** 5 — operacional
**Período:** Dia apenas

Antenas, transponders, relay Terra-Marte. Na NASA, communications officer é papel
secundário do commander — sem dedicação exclusiva em missões de 6 pessoas.
Desliga à noite por ser operacional e não crítico. Valor SIMULATED.

---

### SCI-01 Science Lab — 15 kW
**Responsável:** Scientist
**Prioridade:** 6 — operacional
**Período:** Dia apenas

15 kW = 10 kW fixo (infraestrutura do laboratório) + 5 kW por cientista ativo (1).
Laboratório científico de superfície: análise de amostras, espectrometria, microscopia.
Valor SIMULATED por analogia com laboratório remoto automatizado.

---

### LOG-01 Logistics — 15 kW
**Responsável:** Pilot (papel primário em missão de superfície)
**Prioridade:** 7 — operacional
**Período:** Dia apenas

Carregamento de rovers, armazenamento pressurizado, suporte a EVA (atividade
extraveicular). O piloto assume papel de operador de logística na superfície —
padrão da DRA 5.0 para missões sem retorno imediato. Valor SIMULATED.

---

### MIN-01 ISRU Mining — 40 kW
**Responsável:** Engineer Power/ISRU (compartilha domínio de energia com PWR-01)
**Prioridade:** 8 — primeiro a desligar
**Período:** Dia apenas

Extração in-situ de O₂ e H₂O do regolito marciano. Missão inicial opera sem
produção de propelente em escala — consumo reduzido de 40 kW (vs 100 kW de
operação completa descrita em Space Science & Technology, 2021).

O engenheiro de energia supervisiona naturalmente o ISRU porque ambos compartilham
o mesmo domínio: quem gerencia as fontes de geração também gerencia o maior consumidor.
