
# US-071 — HA/DR e Backup
**Como** Operação  
**Quero** RPO/RTO definidos e restauração granular  
**Para** continuidade de negócios

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Teste de restauração
Dado um backup incremental
Quando executo restauração parcial
Então recuperar itens por classe/regra com sucesso
