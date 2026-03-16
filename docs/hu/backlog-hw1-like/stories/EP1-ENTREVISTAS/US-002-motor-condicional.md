
# US-002 — Motor de Perguntas Condicionais
**Como** Entrevistador  
**Quero** navegar por perguntas com validações e branching (IF/ELSE)  
**Para** coletar somente o necessário e reduzir retrabalho

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Validação de obrigatoriedade
Dado que estou na pergunta "Prazo contratual (meses)"
Quando deixo em branco
Então devo ver um erro "Campo obrigatório" e não prosseguir

Cenário: Branching por tipo documental
Dado resposta "Tipo = Contrato de Prestação"
Quando avanço
Então exibir bloco "Eventos de início" com "término do contrato" como opção padrão
