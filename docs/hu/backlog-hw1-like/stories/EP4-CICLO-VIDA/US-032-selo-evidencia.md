
# US-032 — Selo de Evidência e Pacote de Auditoria
**Como** Compliance  
**Quero** selo (hash + timestamp + usuário + razão)  
**Para** comprovar integridade de decisões

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Consulta de auditoria
Dado um conjunto de decisões
Quando solicito o pacote
Então gerar JSON com trilhas e metadados
