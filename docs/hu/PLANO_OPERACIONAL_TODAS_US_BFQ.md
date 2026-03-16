# 🧩 Plano Operacional — Todas as US (Backend / Frontend / QA)

**Data:** 10/03/2026  
**Escopo:** execução interna objetiva  
**Base:** sequência definida em `PLANO_SPRINT_ENXUTO_TODAS_US.md`

---

## Como usar

- Cada US tem 3 trilhas: **B** (backend), **F** (frontend), **Q** (QA).
- O time pode executar em paralelo quando a dependência da US estiver liberada.
- Para UI, manter identidade visual HW1 (tokens/componentes do design system).
- Execução diária detalhada por sprint: `docs/hu/CHECKLIST_DIARIO_SPRINTS_S1_A_S5.md`.

---

## S1 — Fundação Funcional

| US | B (Backend) | F (Frontend) | Q (QA) |
|---|---|---|---|
| US-001 | Modelar roteiro/pergunta/versão; expor CRUD e versionamento com validações. | Entregar catálogo e editor de roteiros com estados de carregamento/erro. | Validar criação, edição, versionamento e bloqueios de campos obrigatórios. |
| US-002 | Implementar engine condicional (IF/ELSE) e endpoint de execução/dry-run. | Construir fluxo de entrevista condicional com navegação por ramificação. | Cobrir cenários de branching, obrigatoriedade e mensagens de validação. |
| US-003 | Implementar upload, hash, metadados e vínculo de evidência à resposta. | Criar UI de anexos com progresso, erro e associação ao item da entrevista. | Validar tipos de arquivo, vínculo correto e rastreabilidade do anexo. |
| US-010 | Implementar árvore PCD (função→atividade→série→classe) com CRUD completo. | Entregar construtor hierárquico com navegação e formulários de cadastro. | Testar CRUD da árvore, consistência de hierarquia e regras de unicidade. |
| US-020 | Implementar regras de retenção, evento inicial e cálculo de datas-alvo. | Criar tela de cadastro/simulação de regra com visualização de resultados. | Validar cálculos de prazo, exceções básicas e persistência da regra. |

---

## S2 — Núcleo Operacional de Decisão

| US | B (Backend) | F (Frontend) | Q (QA) |
|---|---|---|---|
| US-022 | Implementar geração de ordem/termo e fluxo de aprovação com evidências. | Entregar tela de análise/aprovação e emissão de termo para operação. | Validar trilha 4-olhos, geração de termo e integridade dos registros. |
| US-031 | Implementar máquina de estados, SLA e regras de transição do workflow. | Criar painel de tarefas por estado com ações de aprovar/rejeitar. | Validar transições válidas, SLA e bloqueio de ações indevidas. |
| US-090 | Implementar serviços de resumo/prévia e integração com regras existentes. | Entregar assistente com progresso, resumo final e prévia PCD/TTD. | Validar usabilidade do fluxo completo e coerência das sugestões exibidas. |
| US-040 | Implementar consultas de rastreabilidade e API de drill-down. | Construir matriz visual com filtros e navegação para detalhe. | Validar filtros, consistência do drill-down e resposta por cenários críticos. |
| US-004 | Implementar serviço de sugestão classe/metadado com justificativa. | Exibir sugestões com aceite/ajuste manual no pós-entrevista. | Validar qualidade mínima das sugestões e fluxo de ajuste manual. |

---

## S3 — Governança Aplicada

| US | B (Backend) | F (Frontend) | Q (QA) |
|---|---|---|---|
| US-011 | Implementar versão aprovada somente leitura e histórico comparável. | Entregar interface de comparação e aprovação de versões PCD. | Validar congelamento de versão e rastreabilidade das mudanças. |
| US-012 | Implementar perfil de metadados obrigatórios e regras por classe. | Criar formulário de metadados/segurança com validações de obrigatoriedade. | Validar regras por classe e bloqueio de salvamento incompleto. |
| US-021 | Implementar legal hold/exceção suspendendo e retomando prazos. | Entregar painel para aplicar/remover hold com justificativa. | Validar suspensão de prazo e auditoria da ação por usuário. |
| US-032 | Implementar geração/consulta de pacote de auditoria com selo. | Criar busca/visualização de pacote de auditoria por item/decisão. | Validar integridade do pacote e rastreabilidade do selo exibido. |
| US-052 | Implementar importação com mapeamento de campos e validação por lote. | Entregar wizard de importação com etapa de mapeamento e revisão. | Validar lote com sucesso/erro parcial e relatório de inconsistências. |
| US-060 | Implementar políticas RBAC/ABAC e avaliação de acesso por atributo. | Criar painel de perfis/políticas com escopo por unidade/sigilo. | Validar matriz de permissões e segregação de funções. |

---

## S4 — Escala Operacional

| US | B (Backend) | F (Frontend) | Q (QA) |
|---|---|---|---|
| US-070 | Implementar coleta de métricas, SLO e gatilhos de alerta. | Entregar dashboard operacional de telemetria com visão mínima de saúde. | Validar alertas em limiar e coerência dos indicadores exibidos. |
| US-080 | Implementar cálculo de score de qualidade e regras de avaliação. | Criar visão de inventário com score, filtros e destaques de risco. | Validar score por amostragem e consistência dos resultados. |
| US-081 | Implementar planejamento por ondas com dependências e cronograma. | Entregar painel de ondas com sequência e impacto por unidade. | Validar encadeamento de ondas e atualização de estados planejados. |
| US-091 | Implementar serviços de trilha/template e registro de consumo interno. | Criar portal de conhecimento com trilhas, templates e busca. | Validar acesso a conteúdo, download e trilha de uso básica. |
| US-030 | Implementar scheduler idempotente para retenção e log de execução. | Entregar painel simples de janelas de execução e status de job. | Validar idempotência e não duplicação em reprocessamento. |

---

## S5 — Hardening Técnico

| US | B (Backend) | F (Frontend) | Q (QA) |
|---|---|---|---|
| US-041 | Implementar hashchain/WORM e endpoint de verificação de integridade. | Entregar tela de verificação e status de conformidade de logs. | Validar detecção de inconsistência e emissão de alerta. |
| US-050 | Consolidar APIs REST/GraphQL com autenticação, paginação e limites. | Entregar área interna de consulta de contratos API (catálogo básico). | Validar contrato API, autenticação e cenários de erro padrão. |
| US-051 | Implementar publicação de eventos e assinatura de payload. | Criar painel de monitoramento de eventos e reprocessamento controlado. | Validar entrega, retry e consistência de payload assinado. |
| US-061 | Implementar criptografia, marcação LGPD e anonimização aplicável. | Entregar tela administrativa de políticas e status de proteção de dados. | Validar controles LGPD e comportamento de anonimização. |
| US-071 | Implementar rotina de backup/restauração parcial com trilha de execução. | Criar interface de acionamento/consulta de restauração operacional. | Validar recuperação parcial e evidência mínima de teste DR. |

---

## Critério de encerramento por sprint

- Todas as US da sprint com cenários críticos validados em ambiente interno.
- Pendências residuais registradas no board com responsável e prazo curto.
- Changelog objetivo publicado (sem relatório extenso).