# ✅ Checklist Diário Executável — Sprints S1 a S5

**Data:** 10/03/2026  
**Escopo:** execução interna (26 US)  
**Base de planejamento:** `PLANO_SPRINT_ENXUTO_TODAS_US.md` e `PLANO_OPERACIONAL_TODAS_US_BFQ.md`

---

## Regras rápidas de uso

- Cada sprint considera **10 dias úteis**.
- Cada dia fecha com atualização objetiva no board (Done / Impedimento / Próximo passo).
- UI segue identidade visual HW1 obrigatoriamente.
- QA valida cenários críticos no mesmo sprint (sem acumular para sprint seguinte).

---

## S1 — Fundação Funcional (US-001, US-002, US-003, US-010, US-020)

| Dia | Backend | Frontend | QA | Saída esperada |
|---|---|---|---|---|
| D1 | Refinar contratos API e modelo de dados das 5 US. | Preparar estrutura de páginas/componentes base. | Preparar checklist de aceite por US. | Sprint detalhada e sem lacunas de escopo. |
| D2 | Implementar núcleo US-001 (CRUD/versionamento). | Tela catálogo/editor inicial US-001. | Casos de teste US-001 definidos. | Fluxo mínimo de roteiro disponível. |
| D3 | Implementar motor condicional base US-002. | Fluxo entrevista condicional inicial US-002. | Testes de branching preparados. | Ramificação inicial funcional. |
| D4 | Implementar upload/hash US-003. | UI de anexos/progresso US-003. | Testes de anexos e vínculo. | Evidência vinculada à resposta. |
| D5 | Implementar árvore PCD US-010 (CRUD base). | UI de árvore/formulário US-010. | Testes CRUD de hierarquia. | PCD navegável com criação/edição. |
| D6 | Implementar cálculo de retenção US-020. | Tela regra/simulação US-020. | Casos de cálculo de prazo. | Simulação de regra funcionando. |
| D7 | Integrar US-001↔US-002↔US-003. | Ajustar estados de erro/loading HW1. | Rodada funcional integrada (parcial). | Fluxo entrevista + evidências coeso. |
| D8 | Correções backend e ajustes de contrato API. | Correções de UX e validações de formulário. | Execução completa de cenários críticos S1. | Lista objetiva de bugs priorizados. |
| D9 | Fechar bugs críticos e hardening técnico. | Fechar bugs críticos de interface. | Regressão curta das 5 US. | Sprint pronta para validação interna. |
| D10 | Apoio à demo interna e publicação changelog. | Apoio à demo interna e checklist visual HW1. | Sinalizar aceite final por US. | S1 encerrada com aceite interno. |

---

## S2 — Núcleo de Decisão (US-022, US-031, US-090, US-040, US-004)

| Dia | Backend | Frontend | QA | Saída esperada |
|---|---|---|---|---|
| D1 | Refinar dependências das 5 US e sequência técnica. | Definir wireflows operacionais prioritários. | Atualizar matriz de testes da sprint. | Planejamento executável validado. |
| D2 | Núcleo de ordem/termo US-022. | Tela de análise/aprovação US-022. | Testes de aprovação 4-olhos. | Ordem/termo gerável. |
| D3 | Máquina de estados e SLA US-031. | Painel de tarefas por estado US-031. | Testes de transição de workflow. | Workflow com estados válidos. |
| D4 | Serviço de resumo/prévia US-090. | Assistente com progresso/resumo US-090. | Testes de fluxo ponta a ponta assistido. | Assistente operacional interno. |
| D5 | API de rastreabilidade/drill-down US-040. | Matriz visual e filtros US-040. | Testes de consulta e drill-down. | Matriz de rastreabilidade disponível. |
| D6 | Serviço de sugestão US-004 com justificativa. | Tela de sugestões com ajuste manual US-004. | Testes de aceite/ajuste de sugestão. | Sugestão automática usável. |
| D7 | Integração US-022↔US-031↔US-040. | Ajustes de consistência visual HW1 entre módulos. | Rodada integrada dos fluxos críticos. | Jornada de decisão estabilizada. |
| D8 | Correções de regra/consistência de dados. | Correções de usabilidade e mensagens. | Reexecução de cenários críticos S2. | Qualidade funcional consolidada. |
| D9 | Hardening e fechamento de pendências técnicas. | Hardening de UI e acessibilidade essencial. | Regressão curta da sprint. | Sprint pronta para aceite. |
| D10 | Demo interna e publicação de changelog. | Demo interna com cenários principais. | Aceite final e pendências residuais no board. | S2 encerrada com visibilidade clara. |

---

## S3 — Governança Aplicada (US-011, US-012, US-021, US-032, US-052, US-060)

| Dia | Backend | Frontend | QA | Saída esperada |
|---|---|---|---|---|
| D1 | Refinar integração de segurança e metadados entre US. | Planejar telas administrativas e de auditoria. | Preparar suíte de testes de governança. | Sprint alinhada por risco e prioridade. |
| D2 | Versionamento/aprovação PCD US-011. | UI de comparação/aprovação US-011. | Testes de versão somente leitura. | Fluxo de versão controlado. |
| D3 | Metadados obrigatórios/regras US-012. | Formulário de metadados com validações US-012. | Testes de obrigatoriedade por classe. | Controle de metadados consistente. |
| D4 | Legal hold/exceções US-021. | Painel de aplicação/remoção de hold US-021. | Testes de suspensão/retomada de prazo. | Hold funcional com rastreio. |
| D5 | Pacote de auditoria/selo US-032. | Busca e visualização de auditoria US-032. | Testes de integridade de pacote. | Evidência auditável consultável. |
| D6 | Importação/mapeamento por lote US-052. | Wizard de importação e revisão US-052. | Testes de lote com erro parcial. | Importação operacional estável. |
| D7 | Políticas RBAC/ABAC US-060. | Painel de perfis/políticas US-060. | Testes de permissão por perfil/atributo. | Segurança administrativa aplicada. |
| D8 | Integração e correções de governança/sigilo. | Correções de UX administrativa HW1. | Execução completa de cenários críticos S3. | Governança funcional consolidada. |
| D9 | Fechamento de bugs críticos e hardening. | Fechamento de inconsistências visuais/fluxo. | Regressão curta da sprint. | S3 pronta para aceite interno. |
| D10 | Demo interna e changelog objetivo. | Apoio à demo com trilhas de validação. | Aceite final + registro de pendências residuais. | S3 encerrada sem débito oculto. |

---

## S4 — Escala Operacional (US-070, US-080, US-081, US-091, US-030)

| Dia | Backend | Frontend | QA | Saída esperada |
|---|---|---|---|---|
| D1 | Refinar arquitetura operacional (telemetria, migração, scheduler). | Planejar dashboards e portais de operação. | Montar testes focados em operação contínua. | Sprint preparada para escala. |
| D2 | Métricas/SLO/alerta US-070. | Dashboard de saúde US-070. | Testes de limiar e alerta. | Observabilidade mínima ativa. |
| D3 | Score de qualidade US-080. | Tela inventário/score US-080. | Testes de consistência de score. | Qualidade de dados visível. |
| D4 | Planejamento por ondas US-081. | Painel de ondas/dependências US-081. | Testes de encadeamento de ondas. | Migração planejável por unidade. |
| D5 | Serviços de trilha/template US-091. | Portal de conhecimento US-091. | Testes de acesso e consumo de conteúdo. | Adoção interna habilitada. |
| D6 | Scheduler idempotente US-030. | Painel de execução de janelas US-030. | Testes de reprocessamento sem duplicidade. | Motor operacional previsível. |
| D7 | Integração US-070↔US-030 e ajustes operacionais. | Ajuste de consistência visual entre painéis. | Rodada integrada dos cenários críticos. | Operação monitorável ponta a ponta. |
| D8 | Correções técnicas e ajuste de performance. | Correções de UX para uso operacional contínuo. | Reexecução de cenários críticos S4. | Sprint estabilizada. |
| D9 | Hardening e fechamento de pendências técnicas. | Hardening final de interface. | Regressão curta da sprint. | S4 pronta para aceite. |
| D10 | Demo interna e changelog enxuto. | Demo de operação e adoção. | Aceite final e pendências residuais registradas. | S4 encerrada com prontidão operacional. |

---

## S5 — Hardening Técnico (US-041, US-050, US-051, US-061, US-071)

| Dia | Backend | Frontend | QA | Saída esperada |
|---|---|---|---|---|
| D1 | Refinar escopo de hardening e critérios de conformidade. | Planejar telas técnicas de operação/segurança. | Definir suíte final de regressão e compliance. | Sprint com critérios objetivos fechados. |
| D2 | Hashchain/WORM e verificação US-041. | Tela de conformidade de logs US-041. | Testes de integridade com inconsistência simulada. | Integridade auditável visível. |
| D3 | Consolidação APIs US-050. | Catálogo interno de APIs US-050. | Testes de contrato, auth e erros padrão. | APIs estabilizadas para uso interno. |
| D4 | Eventos e assinatura de payload US-051. | Painel de monitoramento/reprocessamento US-051. | Testes de retry e entrega assíncrona. | Trilha de eventos confiável. |
| D5 | Controles LGPD/criptografia US-061. | Painel administrativo de proteção US-061. | Testes de regra LGPD e anonimização. | Segurança de dados validada. |
| D6 | Rotina backup/restauração US-071. | Interface de restauração operacional US-071. | Teste de recuperação parcial com evidência. | Continuidade operacional comprovada. |
| D7 | Integração técnica cruzada das 5 US. | Ajustes finais de consistência visual HW1. | Rodada integrada de cenários críticos S5. | Plataforma endurecida e coerente. |
| D8 | Correções críticas e ajustes de performance/confiabilidade. | Correções finais de UX técnica. | Reexecução de testes de risco alto. | Estabilidade final atingida. |
| D9 | Fechamento técnico, documentação curta interna. | Fechamento visual e estados operacionais finais. | Regressão final da trilha S1→S5. | Pronto para aceite global interno. |
| D10 | Demo interna final e handoff operacional. | Demo final de painéis e fluxos internos. | Aceite final e checklist de encerramento do ciclo. | S5 encerrada com baseline estável. |

---

## Critério de sucesso por dia

- Cada item do dia deve terminar com: **feito**, **evidência curta**, **próximo passo**.
- Impedimento não resolvido em 24h deve ser escalado no board interno.