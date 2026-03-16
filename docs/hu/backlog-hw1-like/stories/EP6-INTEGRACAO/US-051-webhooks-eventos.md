
# US-051 — Eventos Internos
**Como** Módulo Interno  
**Quero** receber eventos de ciclo de vida  
**Para** sincronizar estados e políticas

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Disparo de eventos
Dado aprovação de classe
Quando status mudar para "Aprovado"
Então enviar webhook com payload assinado
