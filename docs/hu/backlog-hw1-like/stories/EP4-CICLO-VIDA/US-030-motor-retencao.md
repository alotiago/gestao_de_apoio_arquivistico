
# US-030 — Motor de Retenção Programável
**Como** Administrador  
**Quero** agendar janelas e obter logs imutáveis  
**Para** processar retenções com segurança e previsibilidade

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Execução idempotente
Dado um job de retenção
Quando reprocesso a mesma janela
Então não devo duplicar ordens geradas
E devo registrar log operacional de sucesso/falha
