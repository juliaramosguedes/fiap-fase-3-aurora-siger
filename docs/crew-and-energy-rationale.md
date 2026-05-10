# Nota de tripulação — Aurora Siger · 6 pessoas

> Rascunho para incorporação ao README.
> Fonte base: NASA DRA 5.0 (Drake, 2009); arXiv:2410.00066 (2024); NASA CR-2024.

---

## Por que 6 pessoas?

A NASA define 6 como o tamanho mínimo seguro para uma missão de longa permanência
em Marte — o número que garante um substituto treinado para cada uma das três
expertises críticas: pilotagem, medicina e engenharia.
(NASA CR-2024 — "Humans to Mars, But How Many?")

A Aurora Siger segue essa mesma arquitetura: cada módulo tem um responsável primário,
e os módulos críticos e essenciais nunca são compartilhados.

---

## Composição da tripulação e módulos sob responsabilidade

| # | Papel (NASA DRA 5.0) | Módulo primário | Prioridade |
|---|---|---|---|
| 1 | Commander | COM-01 Communications | 5 — operacional |
| 2 | Pilot | LOG-01 Logistics | 7 — operacional |
| 3 | Medical Officer | MED-01 Medical | 2 — essencial |
| 4 | Scientist | SCI-01 Science Lab | 6 — operacional |
| 5 | Engineer 1 (ECLSS) | LSS-01 Life Support + HAB-01 Habitat | 1 e 3 — crítico/essencial |
| 6 | Engineer 2 (Power/ISRU) | PWR-01 Power Systems + MIN-01 ISRU Mining | 4 e 8 — essencial/operacional |

Os módulos críticos e essenciais (prioridade 1–4) têm pessoa dedicada ou
compartilham infraestrutura física real:
- LSS-01 e HAB-01 são operados pelos mesmos sistemas de pressão, temperatura e HVAC —
  o mesmo engenheiro gerencia os dois.
- PWR-01 e MIN-01 compartilham o domínio de energia — o engenheiro que gerencia
  as fontes renováveis naturalmente supervisiona o ISRU que consome essa energia.

---

## Por que essa configuração é autossuficiente e sustentável?

**Energia:**
A colônia opera com 3 painéis solares de 1.000 m² e 5 turbinas eólicas de 40 m
de diâmetro — configuração baseada no arXiv:2410.00066, que determina que 3 conjuntos
cobrem 51,7% dos locais de Marte.

Durante o dia (12 h), a geração chega a 498 kW contra 253 kW de consumo —
excedente de +245 kW que carrega o banco de 6 baterias de 312 kWh cada.

À noite (12,6 h), módulos não-essenciais (SCI, LOG, MIN, COM) desligam automaticamente.
O consumo cai para 175 kW. As turbinas eólicas geram 63 kW continuamente.
O déficit noturno de 112 kW é coberto pelas baterias, que têm capacidade usável de
1.498 kWh — suficiente para 13,4 h sem geração adicional.

Em tempestade de areia (solar −85%, vento a 25 m/s), a eólica compensa parcialmente
a queda solar. O sistema ainda gera 357 kW — superando os 253 kW de consumo diurno.
É a complementaridade projetada: quando o sol cai, o vento sobe.

**Autonomia operacional:**
O MGAB toma decisões sem intervenção humana: desliga módulos por ordem de prioridade
quando o balanço energético fica crítico, reativa quando o sistema se recupera, e
emite alertas preditivos antes de qualquer falha. A tripulação foca em ciência e
manutenção; o sistema cuida da energia.

**ISRU como sustentabilidade de longo prazo:**
O MIN-01 extrai O₂ e H₂O do regolito marciano — reduzindo dependência de resuprimento
da Terra. Consome 40 kW (operação inicial, sem produção de propelente em escala).
Em missões futuras, escalaria para 100 kW com produção de propelente completa
(Space Science & Technology, 2021).
