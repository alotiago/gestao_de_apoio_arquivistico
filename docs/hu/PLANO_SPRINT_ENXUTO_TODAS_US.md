# 🚀 Plano de Sprint Enxuto — Todas as US (26/26)

**Data:** 10/03/2026  
**Escopo:** Operação interna (execução objetiva, sem relatório detalhado de entrega externa)  
**Diretriz obrigatória de UI:** toda interface com identidade visual HW1 (tokens, componentes e contraste consistente).

---

## Critério de Pronto Global (aplicável a todas as US)

Uma US é considerada **pronta** quando:
- Critérios de aceite em Gherkin estão implementados e validados no ambiente interno.
- Fluxo funcional está integrado ao backend necessário para a história.
- UI (quando existir) segue HW1, sem classes de cor hardcoded fora do design system.
- Evidências mínimas de validação interna foram registradas (board + changelog curto).

---

## Status de Execução Interna (12/03/2026)

- ✅ S1 concluída (US-001/US-002 base) com backend e frontend operacionais.
- ✅ S2 concluída (US-002/US-003) com builder condicional, wizard de entrevista, anexos/evidências e antivírus.
- 🟨 S3 em evolução com US-004 inicial e US-010/US-011 avançadas:
	- árvore PCD funcional;
	- edição de nível PCD;
	- criação/lista/aprovação de versões com diff visual no frontend;
	- US-012 operacional com metadados obrigatórios, permissões por papel e validação de payload por classe.
- 🟨 Adiantamentos de módulos operacionais além do núcleo inicial:
	- TTD (US-020/US-021/US-022): regras, legal holds, ordens de destinação com dupla aprovação e assinatura de termo;
	- Ciclo de Vida (US-030/US-031/US-032): agendamento e execução idempotente de jobs, transições de workflow, selo de evidência e pacote JSON de auditoria;
	- Integração (US-050/US-051/US-052): camada REST com OpenAPI e rate limit global aplicado em `/api/v1`, eventos internos com payload assinado/retry e importação CSV com mapeamento/validação;
	- Segurança (US-060/US-061): validação RBAC/ABAC por sigilo, papel e unidade integrada ao PCD, além de proteção LGPD com criptografia/masking/anonimização em administração;
	- Observabilidade (US-070): middleware de telemetria, endpoint de resumo operacional e visão de SLOs no dashboard;
	- Continuidade (US-071): snapshots incrementais e restauração parcial por classe/regra com operação via painel administrativo;
	- Dados & Migração (US-080): inventário de qualidade com score por dimensão, regras de cleansing e histórico comparativo para orientar saneamento do acervo importado;
	- Dados & Migração (US-081): cronograma visual de ondas, dependências, checklist de prontidão e rollback operacional por fase;
	- UX & Adoção (US-090): prévia assistida da entrevista com progresso, resumo e recomendação PCD/TTD contextual;
	- UX & Adoção (US-091): base de conhecimento com templates oficiais, guias de preenchimento e trilhas de onboarding com badge;
	- Operação Interna (S15): smoke check operacional multi-módulo (`/health/smoke`), execução guiada no painel de administração e suíte E2E Playwright cobrindo login/dashboard, administração (smoke), entrevistas (dry-run), PCD (metadados) e TTD (hold);
	- Operação Interna (S15): baseline não funcional de carga/segurança executada com `k6`, `Locust` e `OWASP ZAP` baseline no backend, com 0 falhas em carga e 0 médios na superfície `/docs` após hardening;
	- Governança (US-040/US-041): matriz, logs e verificação de integridade.
- ✅ Cobertura técnica atualizada com testes de integração para EP1–EP10 (incluindo US-050, US-051, US-052, US-060, US-061, US-070, US-071, US-080, US-081, US-090 e US-091) e suíte verde na execução corrente.
- ✅ Backlog funcional das 26 US operacionalizado e validado no escopo interno atual.
- ✅ Sprint 15 validada tecnicamente: smoke check backend `ok`, suíte E2E crítica multi-módulo verde, build/lint frontend verdes, 17 testes de módulos backend passando e baseline de carga/segurança reexecutada com 0 falhas e apenas warnings residuais não bloqueantes no ZAP.

---

## Ordem, Dependências e Definição de Pronto por US

| Ordem | US | Sprint-alvo | Dependências principais | Definição de pronto por US |
|---|---|---|---|---|
| 1 | US-001 | S1 | — | Catálogo/versionamento de roteiros operando com criação e edição válidas. |
| 2 | US-002 | S1 | US-001 | Fluxo condicional (IF/ELSE) com validações de obrigatoriedade funcionando ponta a ponta. |
| 3 | US-003 | S1 | US-002 | Anexos/evidências com vínculo à resposta, metadados e retorno de status no fluxo. |
| 4 | US-010 | S1 | — | Árvore PCD (função→atividade→série→classe) com CRUD estável e navegação clara. |
| 5 | US-020 | S1 | US-010 | Regras de retenção com evento de início e cálculo de prazo aplicados corretamente. |
| 6 | US-022 | S2 | US-020 | Ordem/termo de destinação gerados com trilha de aprovação e evidência associada. |
| 7 | US-031 | S2 | US-022 | Workflow de avaliação com estados, SLA e controle de dupla aprovação ativo. |
| 8 | US-090 | S2 | US-002, US-004 | Assistente de entrevista com progresso, resumo e prévia PCD/TTD em uso interno. |
| 9 | US-040 | S2 | US-010, US-020, US-022 | Matriz de rastreabilidade com consulta e drill-down entregando visão auditável. |
| 10 | US-004 | S2 | US-002, US-010 | Sugestão automática de classes/metadados exibida com justificativa e ajuste manual. |
| 11 | US-011 | S3 | US-010 | Versionamento/aprovação do PCD com histórico e bloqueio de edição na versão aprovada. |
| 12 | US-012 | S3 | US-010, US-060 | Metadados de controle e segurança configuráveis por classe com validação obrigatória. |
| 13 | US-021 | S3 | US-020 | Legal hold/exceções suspendendo prazos com rastreabilidade da decisão. |
| 14 | US-032 | S3 | US-022, US-031 | Pacote de auditoria e selo de evidência consultáveis por registro/decisão. |
| 15 | US-052 | S3 | US-050 | Importação de acervo com mapeamento de campos e relatório de erros/sucessos. |
| 16 | US-060 | S3 | — | Políticas RBAC/ABAC aplicadas com segregação de função e teste de acesso por perfil. |
| 17 | US-070 | S4 | US-030, US-050 | Dashboard de telemetria/SLO com alertas mínimos de operação interna. |
| 18 | US-080 | S4 | US-052 | Inventário e score de qualidade gerando visão de completude/duplicidade acionável. |
| 19 | US-081 | S4 | US-080 | Planejamento de migração por ondas com cronograma e dependências registradas. |
| 20 | US-091 | S4 | US-090 | Base de conhecimento com trilhas e templates disponíveis para adoção interna. |
| 21 | US-030 | S4 | US-020, US-022 | Motor de retenção agendável executando janelas sem duplicação de processamento. |
| 22 | US-041 | S5 | US-040, US-030 | Verificação de integridade de logs (WORM/hashchain) com alerta de inconsistência. |
| 23 | US-050 | S5 | US-010, US-020, US-022 | APIs principais publicadas para consumo interno com autenticação e contrato estável. |
| 24 | US-051 | S5 | US-050 | Eventos/webhooks internos disparados com payload assinado e consumo validado. |
| 25 | US-061 | S5 | US-060 | Controles LGPD/criptografia e anonimização aplicados conforme política definida. |
| 26 | US-071 | S5 | US-070 | Rotina de backup/restauração validada com teste de recuperação parcial bem-sucedido. |

---

## Sequência enxuta por sprint

- **S1 (fundação funcional):** US-001, US-002, US-003, US-010, US-020.
- **S2 (núcleo operacional de decisão):** US-022, US-031, US-090, US-040, US-004.
- **S3 (governança aplicada):** US-011, US-012, US-021, US-032, US-052, US-060.
- **S4 (escala operacional):** US-070, US-080, US-081, US-091, US-030.
- **S5 (hardening técnico):** US-041, US-050, US-051, US-061, US-071.

---

## Observação de execução

- Caso uma dependência técnica atrase, replanejar no board interno sem gerar documentação extra; manter apenas atualização objetiva de sprint e changelog curto.
- Quebra operacional detalhada (Backend/Frontend/QA) disponível em `docs/hu/PLANO_OPERACIONAL_TODAS_US_BFQ.md`.