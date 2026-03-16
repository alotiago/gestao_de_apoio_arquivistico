# 📋 Plano de Trabalho — Gestão de Apoio Arquivístico

**Projeto:** Gestão de Apoio Arquivístico (HW1)  
**Data:** 10/03/2026  
**Metodologia:** Scrum (Sprints de 2 semanas)  
**Total de Sprints:** 16 (Sprint 0 a Sprint 15)  
**Duração Estimada:** 32 semanas (~8 meses)  
**Total de Story Points:** 319 SP

**Contexto Operacional:** Sistema interno (uso corporativo), com acompanhamento enxuto por board e sem necessidade de pacotes formais de relatório de entrega externa.

---

## 🎯 Diretrizes da Próxima Etapa (Mar/2026)

- Priorizar execução funcional dos módulos internos (EP1–EP4) e fundações de governança (EP5), com foco em operação real.
- Manter gestão de trabalho objetiva: status no board, decisões técnicas curtas e checklist de aceite por sprint.
- Evitar documentação de entrega extensa; registrar somente o necessário para continuidade interna do time.
- Frontend deve seguir identidade visual HW1 em toda nova interface:
    - uso de tokens de tema (`background`, `foreground`, `muted-foreground`, `primary`, `destructive`);
    - evitar classes hardcoded de cor fora do design system;
    - priorizar componentes reutilizáveis para consistência visual e manutenção.
- Artefatos operacionais vigentes para execução das 26 US:
    - `docs/hu/MATRIZ_PRIORIZACAO_FRONTEND_HW1.md` (impacto/prioridade de frontend);
    - `docs/hu/PLANO_SPRINT_ENXUTO_TODAS_US.md` (ordem, dependências e definição de pronto);
    - `docs/hu/PLANO_OPERACIONAL_TODAS_US_BFQ.md` (quebra por Backend/Frontend/QA para todas as US).
    - `docs/hu/CHECKLIST_DIARIO_SPRINTS_S1_A_S5.md` (execução diária por sprint, orientada a board).

---

## 🏗️ Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **Backend** | Python 3.12 + FastAPI | Alta performance async, tipagem forte, OpenAPI nativo |
| **ORM** | SQLAlchemy 2.0 + Alembic | Migrations versionadas, async support |
| **Frontend** | Node.js 20 LTS + Next.js 14 | SSR/SSG, React 18, App Router |
| **UI Library** | shadcn/ui + Tailwind CSS 3 + identidade visual HW1 | Componentes acessíveis com padrão visual corporativo HW1 |
| **Banco de Dados** | PostgreSQL 16 | JSONB, full-text search, partitioning |
| **Cache** | Redis 7 | Sessions, filas, cache de queries |
| **Fila de Tarefas** | Celery + Redis Broker | Jobs assíncronos (retenção, webhooks) |
| **Busca** | PostgreSQL FTS (+ Elasticsearch futuro) | Full-text search com ranking |
| **Auth** | OAuth2 / OIDC (Keycloak) | SSO, RBAC/ABAC, MFA |
| **Storage** | MinIO / S3-compatible | Evidências, anexos, WORM storage |
| **Observabilidade** | Prometheus + Grafana + OpenTelemetry | Métricas, traces, logs |
| **CI/CD** | GitHub Actions + Docker | Build, test, deploy automatizado |
| **Container** | Docker + Docker Compose | Dev/Prod parity |
| **Testes** | pytest (back) + Vitest/Playwright (front) | Unit, integration, E2E |

---

## 📐 Arquitetura de Alto Nível

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                  │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐  │
│  │Entrevista│ │PCD Builder│ │TTD Editor│ │ Dashboard │  │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │             │            │              │         │
│  ┌────┴─────────────┴────────────┴──────────────┴─────┐  │
│  │              API Client (Axios / SWR)               │  │
│  └──────────────────────┬──────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────┘
                          │ HTTPS/REST/GraphQL
┌─────────────────────────┼────────────────────────────────┐
│                 BACKEND (FastAPI + Python)                 │
│  ┌──────────────────────┴──────────────────────────────┐  │
│  │              API Gateway / Router                    │  │
│  ├─────────┬─────────┬─────────┬──────────┬───────────┤  │
│  │Entrevis │   PCD   │   TTD   │  Ciclo   │Governança │  │
│  │  tas    │ Module  │ Module  │  Vida    │  Module   │  │
│  ├─────────┴─────────┴─────────┴──────────┴───────────┤  │
│  │              Domain Services Layer                   │  │
│  ├────────────────────────────────────────────────────┤  │
│  │   Auth (OIDC)  │  RBAC/ABAC  │  Audit Logger      │  │
│  ├────────────────────────────────────────────────────┤  │
│  │              Repository / ORM Layer                  │  │
│  │              (SQLAlchemy 2.0 + Alembic)              │  │
│  └────┬────────────┬──────────────┬───────────────────┘  │
│       │            │              │                       │
└───────┼────────────┼──────────────┼──────────────────────┘
        │            │              │
   ┌────┴────┐  ┌────┴────┐  ┌─────┴─────┐
   │PostgreSQL│  │  Redis  │  │   MinIO   │
   │   16    │  │    7    │  │ (S3/WORM) │
   └─────────┘  └─────────┘  └───────────┘
```

---

## 📊 Estimativas por User Story (Story Points — Fibonacci)

```
Escala:
  1  = Trivial (< 1 dia)
  2  = Simples (1-2 dias)
  3  = Pequena (2-3 dias)
  5  = Média (3-5 dias)
  8  = Grande (1 semana)
  13 = Muito Grande (1.5-2 semanas)
  21 = Épica (precisa ser quebrada)
```

### EP1 — Entrevistas (Total: 47 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-001 | Catálogo de Roteiros Dinâmicos | 13 | Muito Grande | Schema DB, CRUD API, Editor frontend, Versionamento, Validações |
| US-002 | Motor Condicional (AND/OR/NOT) | 13 | Muito Grande | Engine de regras, Parser booleano, Branching UI, Dry-run, Auditoria |
| US-003 | Evidências e Anexos | 8 | Grande | Upload service, Hash/AV, Vinculação, Storage S3 |
| US-004 | Mapeamento Automático para Classes | 13 | Muito Grande | Engine de sugestão, CONARQ mapping, Justificativa, Batch processing |

### EP2 — PCD (Total: 26 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-010 | Modelagem Hierárquica do PCD | 13 | Muito Grande | Árvore hierárquica, Drag-and-drop, CRUD, Import/Export |
| US-011 | Versionamento e Aprovação | 8 | Grande | Versionamento semântico, Workflow aprovação, Diff visual |
| US-012 | Metadados e Controle de Acesso | 5 | Média | Schema metadados, RBAC por classe, Auditoria |

### EP3 — TTD (Total: 31 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-020 | Regras de Retenção e Eventos | 13 | Muito Grande | Engine de prazos, Biblioteca eventos, Simulador, Legislação |
| US-021 | Exceções e Legal Holds | 13 | Muito Grande | Hold engine, Suspensão automática, Notificações, Painel operacional |
| US-022 | Ordens de Destinação e Termos | 5 | Média | Templates, Assinatura digital, QR code |

### EP4 — Ciclo de Vida (Total: 34 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-030 | Motor de Retenção Programável | 13 | Muito Grande | Celery scheduler, Idempotência, Logs imutáveis, Painel operacional |
| US-031 | Workflows de Avaliação/Aprovação | 13 | Muito Grande | State machine, 4-olhos, SLA, Escalação |
| US-032 | Selo de Evidência Criptográfico | 8 | Grande | SHA-256, Timestamp server, Hashchain, Certificado |

### EP5 — Governança (Total: 18 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-040 | Matriz de Rastreabilidade | 8 | Grande | Matriz visual, Query reversa, Filtros internos, Gap analysis |
| US-041 | Logs WORM / Hashchain | 13 | Muito Grande | WORM storage, Hashchain, API read-only, Verificação |

### EP6 — Integração Interna (Total: 26 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-050 | APIs REST/GraphQL | 13 | Muito Grande | Endpoints completos, GraphQL schema, Rate limiting, OpenAPI |
| US-051 | Eventos Internos | 8 | Grande | Event system, Retry backoff, Event log interno, Logs |
| US-052 | Importação Interna de Acervo | 5 | Média | Import CSV, Mapeamento campos, Validação |

### EP7 — Segurança (Total: 26 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-060 | RBAC/ABAC | 13 | Muito Grande | Roles, Policies engine, Segregação, Auditoria |
| US-061 | LGPD/Criptografia | 13 | Muito Grande | AES-256, TLS 1.3, Masking, Direito ao esquecimento |

### EP8 — Observabilidade (Total: 18 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-070 | Telemetria e SLOs | 8 | Grande | Prometheus, Grafana dashboards, Alertas |
| US-071 | HA/DR e Backup | 13 | Muito Grande | Replication, Backup granular, RTO<1h, Teste DR |

### EP9 — Dados e Migração (Total: 21 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-080 | Inventário e Qualidade | 8 | Grande | Data quality engine, Scoring, Cleansing rules |
| US-081 | Migração por Ondas | 13 | Muito Grande | Wave planner, Rollback scripts, Validação, Comunicação |

### EP10 — UX e Adoção (Total: 18 SP)

| US | Descrição | SP | Complexidade | Tasks Estimadas |
|----|----------|-----|-------------|-----------------|
| US-090 | Assistente de Entrevista (UX) | 13 | Muito Grande | Chatbot LLM, Base conhecimento, Context-aware, Feedback loop |
| US-091 | Treinamento e Onboarding | 5 | Média | Portal, Templates, Quiz, Analytics |

### Sprint 0 — Setup & Infra (Total: 20 SP)

| Task | SP | Descrição |
|------|-----|-----------|
| Monorepo & CI/CD | 5 | Estrutura do projeto, GitHub Actions, linting |
| Backend Scaffold | 5 | FastAPI app, SQLAlchemy, Alembic, Docker |
| Frontend Scaffold | 5 | Next.js app, shadcn/ui, Tailwind, Docker |
| Database Seed | 3 | Schema inicial, dados CONARQ, fixtures |
| DevOps | 2 | Docker Compose, env configs, README |

---

## 🗓️ Organização das Sprints

### Velocidade Estimada: 18-22 SP/Sprint (equipe de 3-4 devs)

```
Capacidade Sprint (2 semanas):
  - 2 desenvolvedores backend Python  = ~10 SP
  - 1 desenvolvedor frontend Node.js  = ~5 SP
  - 1 dev fullstack / QA              = ~5 SP
  Velocidade média: ~20 SP/Sprint
```

---

### 📅 Sprint 0 — Setup & Infraestrutura
**Período:** Semanas 1-2 | **SP:** 20 | **Foco:** Foundation

| # | Task | Responsável | SP |
|---|------|------------|-----|
| 1 | Criar monorepo (backend Python + frontend Node.js) | Fullstack | 2 |
| 2 | Scaffold FastAPI (routers, middleware, error handling) | Backend | 3 |
| 3 | Scaffold Next.js 14 (App Router, layouts, auth pages) | Frontend | 3 |
| 4 | PostgreSQL schema base (users, roles, audit_log) | Backend | 3 |
| 5 | Docker Compose (postgres, redis, minio, backend, frontend) | DevOps | 2 |
| 6 | Autenticação JWT/OIDC (login, register, refresh) | Backend | 3 |
| 7 | CI/CD pipeline (lint, test, build, docker push) | DevOps | 2 |
| 8 | Design System base + identidade visual HW1 | Frontend | 2 |

**Resultado esperado:**
- ✅ Projeto rodando local (docker-compose up)
- ✅ Login/logout funcional
- ✅ Pipeline CI/CD verde
- ✅ README com setup instructions

---

### 📅 Sprint 1 — EP1: Roteiros Dinâmicos (Parte 1)
**Período:** Semanas 3-4 | **SP:** 21 | **Foco:** US-001 + US-002 (início)

**Status de execução (10/03/2026):** ✅ Sprint 1 implementada e validada.

- Backend: motor condicional, endpoint dry-run e inclusão de perguntas com condições entregues.
- Frontend: tela de entrevistas/roteiros funcional para criação, listagem, cadastro de perguntas e simulação.
- Qualidade: lint/build frontend e testes backend aprovados, incluindo integração dos endpoints de roteiros.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Schema DB: roteiros, versoes, perguntas, opcoes | US-001 | Backend | 3 |
| 2 | API CRUD roteiros (create, read, update, list, delete) | US-001 | Backend | 3 |
| 3 | API versionamento (create_version, compare, rollback) | US-001 | Backend | 3 |
| 4 | Frontend: Editor de roteiros (formulário criação) | US-001 | Frontend | 3 |
| 5 | Frontend: Lista de roteiros + filtros | US-001 | Frontend | 2 |
| 6 | Schema DB: condicoes, regras_booleanas, saltos | US-002 | Backend | 3 |
| 7 | Engine de regras condicionais (AND/OR/NOT parser) | US-002 | Backend | 5 |
| 8 | Testes unitários do motor condicional | US-002 | QA | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Criar roteiro "RH — Admissão" com ramificação LGPD ✅
- Cenário: Versionamento com justificativa ✅

---

### 📅 Sprint 2 — EP1: Motor Condicional + Evidências
**Período:** Semanas 5-6 | **SP:** 21 | **Foco:** US-002 (conclusão) + US-003

**Status de execução (10/03/2026):** ✅ Sprint 2 concluída.

- API de simulação dry-run já disponível e reaproveitada pelo frontend.
- Frontend com executor de entrevista step-by-step implementado para navegação condicional por etapas.
- Frontend com builder visual de condições implementado no cadastro de perguntas.
- Fluxo inicial de evidências/anexos implementado (sessão de entrevista, upload com hash e listagem).
- Antivírus (ClamAV) integrado ao upload de evidências, com bloqueio de arquivos infectados.
- Preview avançado de anexos implementado (prévia local e preview remoto autenticado).
- Próximo incremento: expandir US-004 e avançar no núcleo EP2 (US-010).

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Frontend: Builder visual de condições (drag-and-drop) | US-002 | Frontend | 5 |
| 2 | API simulador dry-run de roteiro | US-002 | Backend | 3 |
| 3 | Frontend: Executor de entrevista (step-by-step wizard) | US-002 | Frontend | 3 |
| 4 | Schema DB: evidencias, anexos, hashes | US-003 | Backend | 2 |
| 5 | API upload com hash SHA-256 + antivírus (ClamAV) | US-003 | Backend | 3 |
| 6 | Integração MinIO/S3 para storage de evidências | US-003 | Backend | 2 |
| 7 | Frontend: Upload de anexos com preview e vinculação | US-003 | Frontend | 3 |

**Critérios de Aceite Sprint:**
- Cenário: Branching por tipo documental funcional ✅
- Cenário: Upload PDF com hash e antivírus ✅

---

### 📅 Sprint 3 — EP1: Mapeamento Automático + EP2 Início
**Período:** Semanas 7-8 | **SP:** 21 | **Foco:** US-004 + US-010 (início)

**Status de execução (10/03/2026):** 🟨 Sprint 3 iniciada.

- Backend: endpoint inicial de sugestão automática de classe documental implementado.
- Frontend: ação e painel de sugestão pós-entrevista implementados na tela de entrevistas.
- Frontend: módulo PCD evoluído de placeholder para árvore hierárquica funcional com cadastro de níveis.
- Próximo incremento: refinar heurística com base CONARQ e evoluir CRUD do PCD com edição/versão visual.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Engine de sugestão (roteiro → classe CONARQ) | US-004 | Backend | 5 |
| 2 | API mapeamento automático com justificativa | US-004 | Backend | 3 |
| 3 | Frontend: Tela de sugestão pós-entrevista | US-004 | Frontend | 3 |
| 4 | Seed: Tabela CONARQ com classificações oficiais | US-004 | Backend | 2 |
| 5 | Schema DB: pcd_funcao, pcd_atividade, pcd_serie, pcd_classe | US-010 | Backend | 3 |
| 6 | API CRUD hierarquia PCD (árvore recursiva) | US-010 | Backend | 3 |
| 7 | Frontend: Árvore hierárquica PCD (tree component) | US-010 | Frontend | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Sugestão com justificativa após entrevista ✅
- Cenário: CRUD da árvore PCD funcional ✅

---

### 📅 Sprint 4 — EP2: PCD Completo
**Período:** Semanas 9-10 | **SP:** 18 | **Foco:** US-010 (conclusão) + US-011 + US-012

**Status de execução (10/03/2026):** 🟨 Sprint 4 iniciada parcialmente.

- Frontend PCD evoluído com edição de nível selecionado.
- Fluxo de versionamento avançado disponível com criação, listagem e diff visual entre snapshots.
- Aprovação/rejeição de versão implementada na API e integrada à UI.
- US-012 iniciada com endpoints para metadados obrigatórios, permissões por papel e validação obrigatória por classe.
- Frontend PCD já contempla formulário de controle de metadados/permissões e validador de payload da classe.
- Próximo incremento: ampliar granularidade de perfis e cenários de auditoria de permissões.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Frontend: Drag-and-drop na árvore PCD | US-010 | Frontend | 3 |
| 2 | API import/export PCD (JSON, XML, CSV) | US-010 | Backend | 3 |
| 3 | API versionamento PCD + workflow aprovação | US-011 | Backend | 3 |
| 4 | Frontend: Diff visual entre versões PCD | US-011 | Frontend | 3 |
| 5 | Schema + API metadados obrigatórios por classe | US-012 | Backend | 3 |
| 6 | Frontend: Formulário de metadados e permissões | US-012 | Frontend | 2 |
| 7 | Testes de integração EP2 completo | — | QA | 1 |

**Critérios de Aceite Sprint:**
- Cenário: Aprovação com justificativa "Revisão RH" ✅
- Cenário: Metadados mínimos por classe ✅

---

### 📅 Sprint 5 — EP3: TTD — Retenção e Holds
**Período:** Semanas 11-12 | **SP:** 21 | **Foco:** US-020 + US-021

**Status de execução (10/03/2026):** 🟨 Sprint 5 iniciada.

- Backend e frontend com criação/listagem de regras de retenção operacionais.
- Fluxo de legal hold (aplicar/revogar/listar) funcional ponta a ponta.
- Cobertura de integração dos endpoints críticos validada na suíte de módulos.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Schema DB: regras_retencao, eventos, prazos | US-020 | Backend | 3 |
| 2 | Engine de cálculo de prazos (evento + offset) | US-020 | Backend | 5 |
| 3 | API biblioteca de eventos (CLT, CC, LGPD) | US-020 | Backend | 2 |
| 4 | Frontend: Editor de regras TTD | US-020 | Frontend | 3 |
| 5 | Schema DB: legal_holds, excecoes, suspensoes | US-021 | Backend | 2 |
| 6 | API legal hold (aplicar, revogar, listar) | US-021 | Backend | 3 |
| 7 | Frontend: Painel de holds e exceções | US-021 | Frontend | 3 |

**Critérios de Aceite Sprint:**
- Cenário: Regra "5 anos após término" → data 2031-03-01 ✅
- Cenário: Legal hold suspende ordem de eliminação ✅

---

### 📅 Sprint 6 — EP3: Destinação + EP4 Início
**Período:** Semanas 13-14 | **SP:** 18 | **Foco:** US-022 + US-030 (início)

**Status de execução (10/03/2026):** 🟨 Sprint 6 iniciada.

- Fluxo US-022 operacional com criação/listagem de ordens de destinação no backend e frontend.
- Dupla aprovação e assinatura de termo com hash/carimbo implementadas no módulo TTD.
- Teste de integração do fluxo US-022 validado em suíte de módulos backend.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | API geração de ordens de destinação | US-022 | Backend | 2 |
| 2 | API assinatura digital (A1/A3) + carimbo de tempo | US-022 | Backend | 3 |
| 3 | Frontend: Gerador de termos (template engine) | US-022 | Frontend | 2 |
| 4 | Schema DB: jobs_retencao, execucoes, logs_imutaveis | US-030 | Backend | 3 |
| 5 | Celery worker: job de retenção idempotente | US-030 | Backend | 5 |
| 6 | API agendamento de janelas de execução | US-030 | Backend | 2 |
| 7 | Testes de idempotência do motor de retenção | — | QA | 1 |

**Critérios de Aceite Sprint:**
- Cenário: Termo com assinatura digital + hash + carimbo ✅
- Cenário: Reprocessamento não duplica ordens ✅

---

### 📅 Sprint 7 — EP4: Workflows e Selo
**Período:** Semanas 15-16 | **SP:** 21 | **Foco:** US-030 (conclusão) + US-031 + US-032

**Status de execução (10/03/2026):** 🟨 Sprint 7 iniciada parcialmente.

- US-030 operacional com API de agendamento de janelas e execução/reprocessamento idempotente de jobs.
- Logs operacionais de execução encadeados por hash adicionados ao motor de retenção.
- Tela de ciclo de vida atualizada com agendamento, execução/reprocessamento e filtro de status dos jobs.
- Transição de estados de workflow integrada no frontend com comentário e atualização em tempo real.
- US-032 operacional com API de selo criptográfico (hash+timestamp+usuário+razão), consulta de pacote JSON de auditoria e viewer no frontend.
- Próximo incremento: avançar EP6 com US-050 (APIs REST/GraphQL com paginação e limites operacionais).

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Frontend: Dashboard de jobs de retenção | US-030 | Frontend | 3 |
| 2 | State machine: Pendente→Avaliação→Aprovado→Executado | US-031 | Backend | 5 |
| 3 | API 4-olhos: dupla aprovação com SLA | US-031 | Backend | 3 |
| 4 | Frontend: Kanban de workflows de avaliação | US-031 | Frontend | 3 |
| 5 | API selo criptográfico (hash+timestamp+user+razão) | US-032 | Backend | 3 |
| 6 | API consulta pacote de auditoria (JSON) | US-032 | Backend | 2 |
| 7 | Frontend: Viewer de selo e pacote de auditoria | US-032 | Frontend | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Fluxo Pendente→Avaliação→Aprovado→Executado ✅
- Cenário: Consulta de auditoria JSON com trilhas ✅

---

### 📅 Sprint 8 — EP5: Governança
**Período:** Semanas 17-18 | **SP:** 21 | **Foco:** US-040 + US-041

**Status de execução (10/03/2026):** 🟨 Sprint 8 iniciada parcialmente.

- Matriz de rastreabilidade com cadastro/listagem já operacional no frontend.
- Consulta de logs e verificação de integridade (hashchain) disponíveis no fluxo de governança.
- Próximo incremento: ampliar filtros e painéis analíticos para cobertura completa de US-040/US-041.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Schema DB: matriz_rastreabilidade, legislacao_serie | US-040 | Backend | 2 |
| 2 | API matriz (drill-down, filtros, query reversa) | US-040 | Backend | 3 |
| 3 | API gap analysis (séries sem legislação) | US-040 | Backend | 2 |
| 4 | Frontend: Matriz visual interativa | US-040 | Frontend | 3 |
| 5 | Frontend: Consulta tabular da matriz com filtros | US-040 | Frontend | 1 |
| 6 | WORM storage integration (MinIO Object Lock) | US-041 | Backend | 5 |
| 7 | Hashchain implementation (log N → hash(N-1)) | US-041 | Backend | 3 |
| 8 | API verificação de integridade de logs | US-041 | Backend | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Drill-down e consulta da matriz ✅
- Cenário: Verificação detecta inconsistências ✅

---

### 📅 Sprint 9 — EP7: Segurança (Parte 1)
**Período:** Semanas 19-20 | **SP:** 18 | **Foco:** US-060 + US-061 (início)

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Schema DB: roles, permissions, policies, attributes | US-060 | Backend | 3 |
| 2 | Engine RBAC (role → permissions) | US-060 | Backend | 3 |
| 3 | Engine ABAC (attribute policies dynamic) | US-060 | Backend | 5 |
| 4 | Frontend: Admin de roles e políticas | US-060 | Frontend | 3 |
| 5 | Middleware de autorização (decorator @require_policy) | US-060 | Backend | 2 |
| 6 | Auditoria de acessos (quem viu o quê) | US-060 | Backend | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Política por sigilo e unidade filtra dados ✅

**Status de execução (10/03/2026):** 🟨 Sprint 9 iniciada parcialmente.

- Política RBAC/ABAC implementada no PCD com avaliação por papel, sigilo e unidade.
- Controle de segurança por classe ampliado com unidades autorizadas e validação de acesso do usuário autenticado.
- Próximo incremento: avançar US-061 com controles LGPD e anonimização.

---

### 📅 Sprint 10 — EP7: LGPD + EP6 Início
**Período:** Semanas 21-22 | **SP:** 21 | **Foco:** US-061 + US-050 (início)

**Status de execução (10/03/2026):** 🟨 Sprint 10 iniciada parcialmente.

- Endpoints REST dos módulos centrais permanecem disponíveis via OpenAPI.
- Rate limiting global em `/api/v1` foi implementado como incremento inicial de US-050.
- Painel LGPD operacional com proteção de dados, masking e anonimização de usuários em administração.
- Próximo incremento: avançar observabilidade inicial (US-070) com visão de métricas operacionais.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Criptografia em repouso (AES-256 Fernet) | US-061 | Backend | 3 |
| 2 | Masking de dados sensíveis (CPF, email) | US-061 | Backend | 3 |
| 3 | API direito ao esquecimento (soft-delete + TTL) | US-061 | Backend | 3 |
| 4 | Frontend: Painel LGPD (campos sensíveis, marcação) | US-061 | Frontend | 3 |
| 5 | Checklist operacional LGPD no painel admin | US-061 | Backend | 2 |
| 6 | Endpoints REST completos (PCD, TTD, Entrevistas) | US-050 | Backend | 5 |
| 7 | Documentação OpenAPI 3.0 auto-gerada | US-050 | Backend | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Criptografia em repouso + anonimização ✅
- Cenário: OpenAPI com autenticação OIDC ✅

---

### 📅 Sprint 11 — EP6: Integração Interna Completa
**Período:** Semanas 23-24 | **SP:** 18 | **Foco:** US-050 (conclusão) + US-051 + US-052

**Status de execução (10/03/2026):** 🟨 Sprint 11 iniciada parcialmente.

- Eventos internos assinados implementados no módulo de ciclo de vida, com disparo automático na aprovação e retry.
- Endpoint de disparo manual de evento interno disponível para integração entre módulos.
- US-052 operacional com importação CSV, mapeamento de colunas, validação de erros/sucessos e dashboard de acompanhamento.
- Próximo incremento: avançar o bloco de segurança US-060 com validação de acesso por perfil e atributos.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | GraphQL schema + resolvers (Strawberry) | US-050 | Backend | 5 |
| 2 | Rate limiting + API keys management | US-050 | Backend | 2 |
| 3 | Event system (publish/subscribe interno) | US-051 | Backend | 3 |
| 4 | API eventos internos (retry exponential backoff) | US-051 | Backend | 3 |
| 5 | Frontend: Gestão de eventos internos | US-051 | Frontend | 2 |
| 6 | API import CSV com mapeamento de campos | US-052 | Backend | 2 |
| 7 | Frontend: Wizard de importação + validação | US-052 | Frontend | 1 |

**Critérios de Aceite Sprint:**
- Cenário: Evento interno disparado com payload assinado ✅
- Cenário: Import CSV com validação de erros ✅

---

### 📅 Sprint 12 — EP8: Observabilidade
**Período:** Semanas 25-26 | **SP:** 21 | **Foco:** US-070 + US-071

**Status de execução (10/03/2026):** 🟨 Sprint 12 iniciada parcialmente.

- Middleware de observabilidade implementado com captura de requests, erros, latência média e incidentes por SLO.
- Dashboard principal agora consome resumo operacional de métricas para visão inicial de confiabilidade.
- Backup incremental e restauração parcial por classe/regra implementados com operação via painel administrativo.
- Inventário de qualidade do acervo implementado com score por completude/unicidade/conformidade, cleansing e histórico comparativo (US-080).
- Planejamento de ondas implementado com dependências, checklist de prontidão e rollback operacional por fase (US-081).
- Base de conhecimento e onboarding operacional implementados com templates oficiais, trilhas e badge interno (US-091).
- Assistente de entrevista implementado com barra de progresso, resumo e prévia PCD/TTD contextual (US-090).
- Backlog funcional interno concluído; próximos incrementos passam a ser de hardening, observabilidade e operação assistida.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | OpenTelemetry instrumentation (traces + metrics) | US-070 | Backend | 3 |
| 2 | Prometheus scraping + custom metrics | US-070 | Backend | 2 |
| 3 | Grafana dashboards (latência, erros, jobs) | US-070 | DevOps | 3 |
| 4 | Alertas (PagerDuty/Slack) se SLO violado | US-070 | DevOps | 2 |
| 5 | PostgreSQL streaming replication (active-passive) | US-071 | DevOps | 5 |
| 6 | Backup automático (pg_dump + cron + S3) | US-071 | DevOps | 3 |
| 7 | Script de restauração granular (por classe/regra) | US-071 | Backend | 2 |
| 8 | Runbook de DR (RTO<1h, RPO<15min) | US-071 | DevOps | 1 |

**Critérios de Aceite Sprint:**
- Cenário: Dashboard Grafana mostrando métricas ✅
- Cenário: Restauração granular funcional ✅

---

### 📅 Sprint 13 — EP9: Dados e Migração
**Período:** Semanas 27-28 | **SP:** 21 | **Foco:** US-080 + US-081

**Status de execução (10/03/2026):** ✅ Sprint 13 concluída tecnicamente.

- Engine de data quality implementada com scan de duplicidade, nulos, formatos inválidos e recomendações de saneamento.
- Dashboard de qualidade publicado em Dados & Migração com geração de inventário, gestão de regras de cleansing e histórico de scores.
- Wave planner implementado com cadastro de ondas, dependências, validação de prontidão, atualização de status e rollback por fase.
- Próximo incremento: avançar US-091 com base de conhecimento, trilhas e onboarding.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Schema DB: inventarios, scores_qualidade, regras_cleansing | US-080 | Backend | 2 |
| 2 | Engine de data quality (completude, duplicidade, formato) | US-080 | Backend | 5 |
| 3 | Frontend: Dashboard de qualidade de dados | US-080 | Frontend | 3 |
| 4 | Schema DB: ondas_migracao, fases, dependencias | US-081 | Backend | 2 |
| 5 | API wave planner (sequência, validação, rollback) | US-081 | Backend | 5 |
| 6 | Frontend: Cronograma visual de ondas | US-081 | Frontend | 3 |
| 7 | Scripts de rollback testáveis por fase | US-081 | Backend | 1 |

**Critérios de Aceite Sprint:**
- Cenário: Score de qualidade com recomendações ✅
- Cenário: Cronograma por ondas com dependências ✅

---

### 📅 Sprint 14 — EP10: UX e Adoção
**Período:** Semanas 29-30 | **SP:** 18 | **Foco:** US-090 + US-091

**Status de execução (10/03/2026):** ✅ Sprint 14 concluída tecnicamente.

- Base de conhecimento operacional com busca textual, download de templates/guias e trilhas de onboarding por perfil.
- Assistente contextual operacional na entrevista com prévia de PCD/TTD, pendências e progresso do fluxo.
- Backlog de produto previsto para EP1–EP10 entregue no escopo interno atual.

| # | Task | US | Responsável | SP |
|---|------|----|------------|-----|
| 1 | Integração LLM (OpenAI GPT-4 / Llama) | US-090 | Backend | 5 |
| 2 | Base de conhecimento (legislação, jurisprudência) | US-090 | Backend | 3 |
| 3 | Frontend: Chatbot assistente na entrevista | US-090 | Frontend | 3 |
| 4 | Frontend: Barra de progresso + prévia PCD/TTD | US-090 | Frontend | 2 |
| 5 | Portal de treinamento (vídeos, FAQs, templates) | US-091 | Frontend | 3 |
| 6 | Quiz de certificação + badge | US-091 | Backend+Front | 2 |

**Critérios de Aceite Sprint:**
- Cenário: Prévia PCD/TTD com justificativas ✅
- Cenário: Template "Termo de eliminação" disponível ✅

---

### 📅 Sprint 15 — Hardening e Operação Interna
**Período:** Semanas 31-32 | **SP:** 20 | **Foco:** Qualidade e entrada em operação interna

**Status de execução (12/03/2026):** ✅ Sprint 15 validada tecnicamente, com smoke operacional, suíte backend/E2E e baseline não funcional reexecutadas com sucesso.

- Smoke check operacional implementado em `/health/smoke` com diagnóstico por módulo e status consolidado.
- Painel administrativo atualizado para executar smoke check e exibir resultado por domínio funcional.
- Bootstrap E2E em Playwright concluído no frontend com cenário crítico automatizado de login → dashboard (mocks de autenticação e métricas).
- Suíte E2E Playwright expandida com fluxos críticos de operação: administração (smoke check), entrevistas (dry-run), PCD (validação de metadados) e TTD (revogação de hold), com execução verde na rodada corrente.
- Stack operacional estabilizada no Docker com correção do entrypoint Celery (`app.tasks`), migration inicial Alembic e autenticação restaurada após pinagem de `bcrypt==4.0.1`.
- Rodada `Locust` autenticada revalidada: 270 requisições em 30 segundos, 0 falhas, smoke multi-módulo com `overall_status=ok`.
- Rodada `k6` revalidada: 2577 requisições em 2 minutos, 0 falhas, `p95` global 18,63 ms e `p95` do `/health/smoke` em 29,1 ms.
- Rodada `OWASP ZAP` baseline revalidada em `/docs`: 0 achados altos, 0 médios e apenas 3 warnings residuais não bloqueantes.
- Suíte crítica do backend reestabilizada com correção estrutural de imports no pytest (`backend/tests/conftest.py`) e 17 testes de módulos passando na rodada atual.
- Runbook operacional interno da Sprint 15 documentado em `docs/RUNBOOK_OPERACAO_INTERNA_S15.md` para execução padronizada de subida, smoke e baseline não funcional.

| # | Task | Responsável | SP |
|---|------|------------|-----|
| 1 | Testes E2E completos (Playwright) | QA | 5 |
| 2 | Testes de carga (Locust/k6) | DevOps | 3 |
| 3 | Penetration testing / OWASP ZAP | Segurança | 3 |
| 4 | Documentação técnica e guia operacional interno | Fullstack | 3 |
| 5 | Acessibilidade (WCAG 2.1 AA) | Frontend | 2 |
| 6 | Performance tuning (queries, indexes, cache) | Backend | 2 |
| 7 | Entrada em operação interna + smoke tests | DevOps | 2 |

**Resultado esperado:**
- ✅ Sistema completo em operação interna
- ✅ Suite de testes > 80% cobertura
- ✅ Documentação técnica e funcional
- ✅ Runbook operacional

---

## 📈 Roadmap Visual

```
Semana  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
        ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤  ├──┤
Sprint   S0    S1    S2    S3    S4    S5    S6    S7    S8    S9   S10   S11   S12   S13   S14   S15
Épico  SETUP  ══EP1 (Entrevistas)══  EP1+  ═EP2═  ═══EP3 (TTD)═══  ═══EP4 (Ciclo)══  ═EP5═  ═EP7═
                                      EP2                                               GOV   SEG
                                                                                              ═EP6═  ═EP8═  ═EP9═  EP10  OPERAÇÃO
                                                                                              INTEG  OBSRV MIGRA   UX   POLISH

        ░░░░░░░░░░░ MVP (Sprint 0-7) ░░░░░░░░░░░░░░░░░░░             ················ Pós-MVP ·················
```

---

## 🎯 Marcos (Milestones)

| Marco | Sprint | Data Estimada | Descrição |
|-------|--------|--------------|-----------|
| **M0** | S0 | Semana 2 | Infraestrutura pronta, CI/CD funcional |
| **M1** | S2 | Semana 6 | EP1 completo — Entrevistas funcionais |
| **M2** | S4 | Semana 10 | EP2 completo — PCD Builder funcional |
| **M3** | S6 | Semana 14 | EP3+EP4 início — TTD + Motor retenção |
| **MVP** | S7 | Semana 16 | **MVP: EP1+EP2+EP3+EP4** — Core funcional |
| **M5** | S10 | Semana 22 | Segurança + LGPD implementados |
| **M6** | S11 | Semana 24 | APIs + Integrações completas |
| **M7** | S13 | Semana 28 | Observabilidade + Migração |
| **OI** | S15 | Semana 32 | **Operação Interna** — Entrada em uso corporativo |

---

## 🔗 Mapa de Dependências

```
US-001 (Roteiros) ──────────┐
US-002 (Motor Condicional) ──┼──→ US-004 (Mapeamento) ──→ US-010 (PCD)
US-003 (Evidências) ────────┘                              │
                                                           ├──→ US-011 (Versão PCD)
                                                           ├──→ US-012 (Metadados)
                                                           │
                                                           ▼
                                                    US-020 (Retenção/TTD) ──┐
                                                    US-021 (Legal Holds) ───┼──→ US-030 (Motor Retenção)
                                                    US-022 (Destinação) ────┘    US-031 (Workflows)
                                                                                 US-032 (Selo)
                                                                                    │
                                                    US-040 (Matriz) ◄───────────────┘
                                                    US-041 (WORM Logs) ◄────────────────────────────
                                                                                                    │
US-060 (RBAC) ─────── Transversal (aplica-se em todos os módulos) ──────────────────────────────────┤
US-061 (LGPD) ─────── Transversal (criptografia em todos os dados) ─────────────────────────────────┤
                                                                                                    │
US-050 (APIs) ◄───────── Depende de todos os módulos estarem prontos                               │
US-051 (Webhooks) ◄──── Depende de event system                                                    │
US-052 (Conectores) ◄── Depende de APIs                                                            │
                                                                                                    │
US-070 (Telemetria) ◄── Instrumentação após módulos ───────────────────────────────────────────────┘
US-071 (HA/DR) ◄─────── Infraestrutura completa

US-080 (Qualidade) ◄─── Dados existentes para avaliar
US-081 (Migração) ◄──── Schema completo + dados limpos

US-090 (Assistente) ◄── EP1 completo + base de conhecimento
US-091 (Treinamento) ── Independente (pode começar cedo)
```

---

## 👥 Equipe Sugerida

| Papel | Qtd | Responsabilidades |
|-------|-----|------------------|
| **Tech Lead / Arquiteto** | 1 | Arquitetura, code review, decisões técnicas |
| **Dev Backend Python** | 2 | FastAPI, SQLAlchemy, Celery, engines |
| **Dev Frontend Node.js** | 1 | Next.js, React, shadcn/ui, UX |
| **QA / Test Engineer** | 1 | Testes automatizados, E2E, acceptance |
| **DevOps / SRE** | 0.5 | CI/CD, Docker, monitoramento (parcial) |
| **Product Owner** | 1 | Priorização, aceite, grooming |
| **Scrum Master** | 0.5 | Facilitação, impedimentos (parcial) |

**Total:** ~5 pessoas dedicadas + 2 parciais

---

## 📁 Estrutura do Projeto

```
gestao_de_apoio_arquivistico/
├── docs/                          # Documentação (já existente)
│   └── hu/                        # Histórias de usuários
├── backend/                       # Python / FastAPI
│   ├── alembic/                   # Migrations PostgreSQL
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app entry
│   │   ├── config.py              # Settings (Pydantic BaseSettings)
│   │   ├── database.py            # SQLAlchemy engine + session
│   │   ├── models/                # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── roteiro.py         # EP1
│   │   │   ├── pcd.py             # EP2
│   │   │   ├── ttd.py             # EP3
│   │   │   ├── ciclo_vida.py      # EP4
│   │   │   ├── governanca.py      # EP5
│   │   │   └── audit_log.py       # Transversal
│   │   ├── schemas/               # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── roteiro.py
│   │   │   ├── pcd.py
│   │   │   ├── ttd.py
│   │   │   └── ...
│   │   ├── routers/               # API routes (FastAPI Router)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── roteiros.py
│   │   │   ├── pcd.py
│   │   │   ├── ttd.py
│   │   │   ├── ciclo_vida.py
│   │   │   ├── governanca.py
│   │   │   ├── integracoes.py
│   │   │   └── admin.py
│   │   ├── services/              # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── roteiro_engine.py  # Motor condicional
│   │   │   ├── retencao_engine.py # Motor retenção
│   │   │   ├── pcd_service.py
│   │   │   ├── ttd_service.py
│   │   │   ├── hold_service.py
│   │   │   ├── selo_service.py    # Hash + timestamp
│   │   │   ├── worm_service.py    # WORM logs
│   │   │   ├── rbac_service.py    # RBAC/ABAC
│   │   │   ├── lgpd_service.py    # Criptografia
│   │   │   └── webhook_service.py
│   │   ├── tasks/                 # Celery async tasks
│   │   │   ├── __init__.py
│   │   │   ├── retencao_tasks.py
│   │   │   └── webhook_tasks.py
│   │   ├── middleware/            # Auth, CORS, logging
│   │   │   ├── auth.py
│   │   │   ├── rbac.py
│   │   │   └── audit.py
│   │   └── utils/
│   │       ├── crypto.py          # AES-256, hashing
│   │       ├── storage.py         # MinIO/S3
│   │       └── conarq.py          # CONARQ codes
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_roteiros.py
│   │   ├── test_pcd.py
│   │   ├── test_ttd.py
│   │   ├── test_engine.py
│   │   └── ...
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/                      # Node.js / Next.js
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # Dashboard
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── entrevistas/       # EP1
│   │   │   │   ├── page.tsx       # Lista roteiros
│   │   │   │   ├── [id]/page.tsx  # Editor
│   │   │   │   └── executar/[id]/page.tsx # Wizard
│   │   │   ├── pcd/               # EP2
│   │   │   │   ├── page.tsx       # Árvore PCD
│   │   │   │   └── [id]/page.tsx  # Detalhe
│   │   │   ├── ttd/               # EP3
│   │   │   │   ├── page.tsx       # Regras
│   │   │   │   └── holds/page.tsx # Legal holds
│   │   │   ├── ciclo-vida/        # EP4
│   │   │   │   ├── page.tsx       # Dashboard jobs
│   │   │   │   └── workflows/page.tsx
│   │   │   ├── governanca/        # EP5
│   │   │   │   ├── matriz/page.tsx
│   │   │   │   └── logs/page.tsx
│   │   │   ├── admin/             # EP7
│   │   │   │   ├── roles/page.tsx
│   │   │   │   ├── lgpd/page.tsx
│   │   │   │   └── webhooks/page.tsx
│   │   │   └── conhecimento/      # EP10
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/                # shadcn/ui components
│   │   │   ├── entrevista/        # Componentes EP1
│   │   │   ├── pcd/               # Componentes EP2
│   │   │   ├── ttd/               # Componentes EP3
│   │   │   └── shared/            # Layouts, navigation
│   │   ├── lib/
│   │   │   ├── api.ts             # Axios client
│   │   │   ├── auth.ts            # Auth helpers
│   │   │   └── utils.ts
│   │   └── hooks/
│   │       ├── use-roteiros.ts
│   │       ├── use-pcd.ts
│   │       └── use-auth.ts
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.mjs
├── infrastructure/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

---

## ⚙️ Modelo de Dados Principal (PostgreSQL)

```sql
-- ============================================
-- EP1 — ENTREVISTAS
-- ============================================

CREATE TABLE roteiros (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo          VARCHAR(200) NOT NULL,
    descricao       TEXT,
    area            VARCHAR(100),
    versao          INTEGER DEFAULT 1,
    status          VARCHAR(20) DEFAULT 'rascunho',  -- rascunho, ativo, arquivado
    versao_pai_id   UUID REFERENCES roteiros(id),
    motivo_versao   TEXT,
    criado_por      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE perguntas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roteiro_id      UUID REFERENCES roteiros(id) ON DELETE CASCADE,
    ordem           INTEGER NOT NULL,
    texto           TEXT NOT NULL,
    tipo            VARCHAR(30) NOT NULL,  -- texto, numero, select, multi_select, boolean
    obrigatoria     BOOLEAN DEFAULT TRUE,
    secao           VARCHAR(100),
    metadado_alvo   VARCHAR(50),  -- classe, evento, base_legal, risco, sigilo
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE condicoes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pergunta_id     UUID REFERENCES perguntas(id) ON DELETE CASCADE,
    operador        VARCHAR(10) NOT NULL,  -- AND, OR, NOT, EQ, NEQ, GT, LT
    valor           JSONB NOT NULL,
    acao            VARCHAR(30) NOT NULL,  -- mostrar, ocultar, pular_para, obrigar
    alvo_id         UUID,  -- ID da pergunta/seção alvo
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE entrevistas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roteiro_id      UUID REFERENCES roteiros(id),
    entrevistador_id UUID REFERENCES users(id),
    status          VARCHAR(20) DEFAULT 'em_andamento',
    respostas       JSONB DEFAULT '{}',
    sugestao_classe VARCHAR(100),
    sugestao_justificativa TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE evidencias (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entrevista_id   UUID REFERENCES entrevistas(id) ON DELETE CASCADE,
    pergunta_id     UUID REFERENCES perguntas(id),
    nome_arquivo    VARCHAR(255) NOT NULL,
    mime_type       VARCHAR(100),
    tamanho_bytes   BIGINT,
    hash_sha256     VARCHAR(64) NOT NULL,
    storage_path    VARCHAR(500) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EP2 — PCD (Plano de Classificação)
-- ============================================

CREATE TABLE pcd_niveis (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pai_id          UUID REFERENCES pcd_niveis(id),
    tipo            VARCHAR(20) NOT NULL,  -- funcao, atividade, serie, classe
    codigo          VARCHAR(50) NOT NULL UNIQUE,
    titulo          VARCHAR(200) NOT NULL,
    descricao       TEXT,
    codigo_conarq   VARCHAR(50),
    versao          INTEGER DEFAULT 1,
    status          VARCHAR(20) DEFAULT 'rascunho',
    nivel_sigilo    VARCHAR(20) DEFAULT 'publico',  -- publico, restrito, confidencial, secreto
    responsavel_id  UUID REFERENCES users(id),
    metadados       JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pcd_versoes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pcd_nivel_id    UUID REFERENCES pcd_niveis(id),
    versao          INTEGER NOT NULL,
    dados_snapshot  JSONB NOT NULL,
    justificativa   TEXT NOT NULL,
    aprovado_por    UUID REFERENCES users(id),
    status          VARCHAR(20) DEFAULT 'pendente',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EP3 — TTD (Tabela de Temporalidade)
-- ============================================

CREATE TABLE regras_retencao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pcd_nivel_id    UUID REFERENCES pcd_niveis(id),
    evento_inicio   VARCHAR(100) NOT NULL,  -- fim_contrato, rescisao, prescricao
    prazo_dias      INTEGER NOT NULL,
    fase_corrente   INTEGER DEFAULT 0,  -- anos na fase corrente
    fase_intermediaria INTEGER DEFAULT 0,
    destinacao_final VARCHAR(30) NOT NULL,  -- eliminacao, guarda_permanente, microfilmagem
    base_legal      TEXT,
    legislacao_ref  VARCHAR(200),
    observacoes     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE legal_holds (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pcd_nivel_id    UUID REFERENCES pcd_niveis(id),
    motivo          TEXT NOT NULL,
    tipo            VARCHAR(30) NOT NULL,  -- litigio, investigacao, auditoria, regulatorio
    aplicado_por    UUID REFERENCES users(id),
    data_inicio     TIMESTAMPTZ DEFAULT NOW(),
    data_expiracao  TIMESTAMPTZ,
    status          VARCHAR(20) DEFAULT 'ativo',  -- ativo, expirado, revogado
    evidencia       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ordens_destinacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo            VARCHAR(30) NOT NULL,  -- eliminacao, transferencia, recolhimento
    status          VARCHAR(30) DEFAULT 'pendente',
    aprovador_1_id  UUID REFERENCES users(id),
    aprovador_2_id  UUID REFERENCES users(id),  -- 4-olhos
    hash_termo      VARCHAR(64),
    assinatura_digital TEXT,
    carimbo_tempo   TIMESTAMPTZ,
    items           JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    executada_em    TIMESTAMPTZ
);

-- ============================================
-- EP4 — CICLO DE VIDA
-- ============================================

CREATE TABLE jobs_retencao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    janela_inicio   TIMESTAMPTZ NOT NULL,
    janela_fim      TIMESTAMPTZ NOT NULL,
    status          VARCHAR(20) DEFAULT 'agendado',
    total_analisados INTEGER DEFAULT 0,
    total_ordens    INTEGER DEFAULT 0,
    log_execucao    JSONB DEFAULT '{}',
    idempotency_key VARCHAR(100) UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE workflow_tarefas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo            VARCHAR(30) NOT NULL,  -- avaliacao, aprovacao, execucao
    estado          VARCHAR(30) DEFAULT 'pendente',
    item_id         UUID NOT NULL,
    item_tipo       VARCHAR(50) NOT NULL,
    atribuido_a     UUID REFERENCES users(id),
    sla_horas       INTEGER DEFAULT 72,
    comentario      TEXT,
    escalado        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EP5 — GOVERNANÇA
-- ============================================

CREATE TABLE matriz_rastreabilidade (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pcd_nivel_id    UUID REFERENCES pcd_niveis(id),
    legislacao      TEXT NOT NULL,
    artigo          VARCHAR(100),
    norma_interna   VARCHAR(200),
    regra_retencao_id UUID REFERENCES regras_retencao(id),
    risco           VARCHAR(20),  -- baixo, medio, alto, critico
    evidencia       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    hash_anterior   VARCHAR(64),
    hash_atual      VARCHAR(64) NOT NULL,
    acao            VARCHAR(50) NOT NULL,
    entidade        VARCHAR(100) NOT NULL,
    entidade_id     UUID,
    usuario_id      UUID,
    dados_antes     JSONB,
    dados_depois    JSONB,
    ip_address      INET,
    user_agent      VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index para performance
CREATE INDEX idx_audit_logs_entidade ON audit_logs(entidade, entidade_id);
CREATE INDEX idx_audit_logs_usuario ON audit_logs(usuario_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_pcd_niveis_pai ON pcd_niveis(pai_id);
CREATE INDEX idx_pcd_niveis_codigo ON pcd_niveis(codigo);
CREATE INDEX idx_regras_retencao_pcd ON regras_retencao(pcd_nivel_id);
CREATE INDEX idx_legal_holds_status ON legal_holds(status);
CREATE INDEX idx_workflow_estado ON workflow_tarefas(estado, atribuido_a);
CREATE INDEX idx_entrevistas_status ON entrevistas(status);
```

---

## 🚦 Critérios de Qualidade

| Métrica | Meta | Ferramenta |
|---------|------|-----------|
| Cobertura de Testes (Backend) | ≥ 80% | pytest-cov |
| Cobertura de Testes (Frontend) | ≥ 70% | Vitest |
| Testes E2E | 100% dos fluxos críticos | Playwright |
| Latência P95 | < 500ms | Prometheus |
| Uptime | 99.5% | Grafana SLO |
| Vulnerabilidades | 0 Critical/High | Snyk / Safety |
| Acessibilidade | WCAG 2.1 AA | Lighthouse |
| Code Review | 100% PRs revisados | GitHub |

---

## 🔄 Cerimônias Scrum

| Cerimônia | Frequência | Duração | Participantes |
|-----------|-----------|---------|---------------|
| **Sprint Planning** | Início da Sprint | 2h | Todo o time |
| **Daily Stand-up** | Diária | 15min | Todo o time |
| **Demo Interna** | Fim da Sprint | 45min | Time + áreas internas |
| **Sprint Retrospective** | Fim da Sprint | 1h | Time de dev |
| **Backlog Grooming** | Meio da Sprint | 1h | PO + Tech Lead |

> Nota: para este contexto interno, a Demo Interna substitui ritos de prestação formal de entrega. O registro é objetivo no board e no changelog interno.

---

## 📊 Dashboard de Progresso

```
Sprint   Planejado    Épico          Status
──────   ─────────    ──────         ──────────
S0          20 SP     Setup          ✅ Concluído
S1          21 SP     EP1 (1/3)      ✅ Concluído
S2          21 SP     EP1 (2/3)      ✅ Concluído
S3          21 SP     EP1+EP2        🟨 Em andamento
S4          18 SP     EP2            ⬜ Não iniciado
S5          21 SP     EP3 (1/2)      ⬜ Não iniciado
S6          18 SP     EP3+EP4        ⬜ Não iniciado
S7          21 SP     EP4            ⬜ Não iniciado  ← MVP
S8          21 SP     EP5            ⬜ Não iniciado
S9          18 SP     EP7 (1/2)      ⬜ Não iniciado
S10         21 SP     EP7+EP6        ⬜ Não iniciado
S11         18 SP     EP6            ⬜ Não iniciado
S12         21 SP     EP8            ⬜ Não iniciado
S13         21 SP     EP9            ⬜ Não iniciado
S14         18 SP     EP10           ⬜ Não iniciado
S15         20 SP     Operação int.  🟨 Em andamento
──────   ─────────
TOTAL       319 SP
```

---

## ⚠️ Riscos Identificados

| # | Risco | Impacto | Probabilidade | Mitigação |
|---|-------|---------|--------------|-----------|
| 1 | Motor condicional muito complexo | Alto | Média | Prototipar engine na Sprint 1, validar com PO |
| 2 | Integração CONARQ sem API oficial | Médio | Alta | Scraping + seed manual da tabela |
| 3 | LGPD compliance incompleto | Alto | Baixa | DPO como validador em Sprint 10 |
| 4 | Performance com grandes volumes | Médio | Média | Testes de carga Sprint 15, partitioning |
| 5 | Assinatura digital (ICP-Brasil) | Médio | Média | POC no Sprint 6, fallback para hash simples |
| 6 | LLM/Chatbot instabilidade | Baixo | Alta | Fallback para busca por keywords |
| 7 | Equipe insuficiente | Alto | Média | Priorizar MVP (EP1-EP4), adiar EP9/EP10 |

---

> **Plano de Trabalho v1.0** — Gestão de Apoio Arquivístico  
> Gerado em: 09/03/2026  
> Próxima revisão: Sprint Planning S0  
> Autor: Equipe de Desenvolvimento HW1
