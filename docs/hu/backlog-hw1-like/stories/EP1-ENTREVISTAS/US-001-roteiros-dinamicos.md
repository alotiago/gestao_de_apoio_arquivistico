
# US-001 — Catálogo de Roteiros Dinâmicos
**Como** Arquivista  
**Quero** cadastrar e versionar roteiros por área/processo com lógica condicional  
**Para** identificar séries documentais, base legal e metadados com precisão

## Critérios de Aceite (Gherkin)
Cenário: Criar roteiro com ramificação por LGPD
Dado que acesso "Roteiros"
Quando crio "RH – Admissão"
E adiciono a pergunta "Contém dados pessoais sensíveis?"
Então devo poder definir que, se "Sim", o sistema exiba o bloco "LGPD" com novas perguntas obrigatórias

Cenário: Versionamento com justificativa
Dado um roteiro aprovado
Quando inicio uma nova versão
Então devo informar motivo da alteração
E a versão anterior permanece apenas leitura

## Observações
- Editor com autosave (30s) e validações de obrigatoriedade
- Cada pergunta mapeia uma decisão (classe, evento, base legal, risco, sigilo)
- Interface deve seguir identidade visual HW1 (tokens de tema e componentes padronizados)
