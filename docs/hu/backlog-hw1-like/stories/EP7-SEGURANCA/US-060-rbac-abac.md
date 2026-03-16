
# US-060 — RBAC/ABAC e Segregação de Funções
**Como** Admin  
**Quero** papéis e políticas por atributo  
**Para** garantir acesso adequado e segregação de funções

## Observações
- Quando houver interface, aplicar identidade visual HW1 (tokens de tema e componentes padronizados).

## Critérios de Aceite (Gherkin)
Cenário: Política por sigilo e unidade
Dado usuários com papéis distintos
Quando defino política por nível de sigilo e unidade
Então apenas perfis autorizados devem acessar os itens
