
# US-011 — Versionamento e Aprovação do PCD
**Como** Gestor  
**Quero** aprovar versões do PCD com justificativa  
**Para** garantir governança e rastreabilidade

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Aprovação com justificativa
Dado um PCD em rascunho
Quando envio para aprovação com justificativa "Revisão RH"
Então a versão aprovada fica somente leitura e a anterior é arquivada
