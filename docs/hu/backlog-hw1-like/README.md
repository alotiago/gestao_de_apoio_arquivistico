
# Backlog — Entrevistas + PCD/TTD + Ciclo de Vida (LGPD/Conformidade)

Este pacote contém personas, épicos, features e histórias com critérios de aceite (Gherkin) para um software de gestão documental com entrevistas assistidas, PCD/TTD e execução do ciclo de vida, incluindo governança, segurança e integrações.

> Contexto de uso: operação interna corporativa, com acompanhamento enxuto por board e sem exigência de relatório formal de entrega externa.

## Como usar
1. Abra esta pasta no VS Code.
2. Instale extensões: "Markdown All in One", "YAML", "Cucumber (Gherkin)".
3. Edite `personas.md`, `epics.yml` e `features.yml` conforme seu contexto.
4. Importe `jira-backlog.csv` no Jira **ou** `azureboards-backlog.csv` no Azure Boards, se desejar.
5. Use as histórias em `/stories` para detalhar critério de aceite e tarefas técnicas.

## Convenções
- IDs no formato `US-XXX`.
- Labels em `labels.json`.
- DoR/DoD em `dor_dod.md`.

## Dicas
- Comece pelos épicos EP1–EP4 (núcleo do MVP).
- Integre com Docz/Eternal nos conectores (EP6).
- Para frontend, aplique identidade visual HW1 em todas as novas telas e refatorações.
