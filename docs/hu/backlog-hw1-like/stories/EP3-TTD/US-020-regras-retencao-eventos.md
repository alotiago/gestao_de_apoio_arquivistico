
# US-020 — Regras de Retenção e Eventos de Início
**Como** Arquivista  
**Quero** cadastrar regras com prazos/fases e eventos de início  
**Para** reger o ciclo de vida documental

## Critérios de Aceite (Gherkin)
Cenário: Regra com evento composto
Dado a classe "Contratos de Prestação"
E a regra "5 anos após término do contrato"
Quando informo "término = 2026-03-01"
Então a data-alvo de eliminação é "2031-03-01", salvo exceções ativas

## Observações
- Editor de regras e simulador de datas devem adotar o padrão visual HW1
