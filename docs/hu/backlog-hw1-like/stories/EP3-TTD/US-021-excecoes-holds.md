
# US-021 — Exceções e Legal Holds
**Como** Jurídico  
**Quero** aplicar legal hold e exceções  
**Para** suspender prazos e mitigar riscos

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Aplicação de legal hold
Dado uma ordem de eliminação aprovada
E um processo judicial relacionado
Quando aplico "legal hold"
Então a ordem é suspensa
E a trilha registra motivo, ator e evidências
