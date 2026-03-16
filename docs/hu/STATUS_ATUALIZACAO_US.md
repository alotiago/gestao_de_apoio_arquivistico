# 📊 Status de Atualização das Histórias de Usuários

**Data de Verificação:** 12/03/2026  
**Total de Histórias:** 26 US  
**Status Geral:** ✅ **TODAS ATUALIZADAS**

**Observação de Escopo:** backlog ajustado para uso interno corporativo, sem exigência de relatórios detalhados de entrega externa.

---

## 📋 Verificação por Épico

### EP1 — Entrevistas (4 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-001** | US-001-roteiros-dinamicos.md | 18 | ✅ COMPLETA | 2 cenários + observações |
| **US-002** | US-002-motor-condicional.md | 13 | ✅ COMPLETA | Lógica booleana definida |
| **US-003** | US-003-evidencias-anexos.md | 9 | ✅ COMPLETA | Rastreabilidade detalhada |
| **US-004** | US-004-mapeamento-classes.md | 10 | ✅ COMPLETA | Mapeamento CONARQ |

---

### EP2 — Classificação de Documentos (3 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-010** | US-010-modelagem-hierarquica.md | 9 | ✅ COMPLETA | Hierarquia Função→Série |
| **US-011** | US-011-versionamento-pcd.md | 9 | ✅ COMPLETA | Versionamento com workflow |
| **US-012** | US-012-metadados-controle.md | 9 | ✅ COMPLETA | RBAC por classe |

---

### EP3 — Tabela de Temporalidade (3 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-020** | US-020-regras-retencao-eventos.md | 10 | ✅ COMPLETA | Prazos com eventos |
| **US-021** | US-021-excecoes-holds.md | 11 | ✅ COMPLETA | Legal holds e exceções |
| **US-022** | US-022-ordens-destinacao-termos.md | 9 | ✅ COMPLETA | Termos assinados |

---

### EP4 — Ciclo de Vida (3 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-030** | US-030-motor-retencao.md | 10 | ✅ COMPLETA | Job scheduler automático |
| **US-031** | US-031-workflows-avaliacao.md | 9 | ✅ COMPLETA | Workflow com SLA |
| **US-032** | US-032-selo-evidencia.md | 9 | ✅ COMPLETA | Selo criptográfico |

---

### EP5 — Governança (2 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-040** | US-040-matriz-rastreabilidade.md | 9 | ✅ COMPLETA | Legislação ↔ Série |
| **US-041** | US-041-logs-worm-hashchain.md | 9 | ✅ COMPLETA | Imutabilidade de logs |

---

### EP6 — Integração (3 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-050** | US-050-apis-rest-graphql.md | 9 | ✅ COMPLETA | APIs para ECM/DMS |
| **US-051** | US-051-webhooks-eventos.md | 9 | ✅ COMPLETA | Eventos assíncronos |
| **US-052** | US-052-conectores-ecm-idm.md | 9 | ✅ COMPLETA | Conectores SAP/Oracle |

---

### EP7 — Segurança (2 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-060** | US-060-rbac-abac.md | 9 | ✅ COMPLETA | Controle granular |
| **US-061** | US-061-lgpd-criptografia.md | 9 | ✅ COMPLETA | LGPD compliance |

---

### EP8 — Observabilidade (2 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-070** | US-070-telemetria-slos.md | 9 | ✅ COMPLETA | SLOs e alertas |
| **US-071** | US-071-ha-dr-backup.md | 9 | ✅ COMPLETA | HA/DR com RTO<1h |

---

### EP9 — Dados e Migração (2 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-080** | US-080-inventario-qualidade.md | 9 | ✅ COMPLETA | Data quality score |
| **US-081** | US-081-estrategia-corte-ondas.md | 9 | ✅ COMPLETA | Migração em 3 phases |

---

### EP10 — UX e Adoção (2 US)

| US | Arquivo | Linhas | Status | Observações |
|----|---------|--------|--------|------------|
| **US-090** | US-090-assistente-entrevista.md | 9 | ✅ COMPLETA | Chatbot assistente |
| **US-091** | US-091-treinamento-base-conhecimento.md | 9 | ✅ COMPLETA | Onboarding + certificação |

---

## 📊 Análise Geral

```
Total de US:           26
US com conteúdo:       26
US vazias:             0
Cobertura:             100% ✅

Linhas médias:         ~10 linhas por US
Formato:               Markdown + Gherkin
Critérios de Aceite:   Presentes em todas
```

---

## ✅ O que cada Histórias Contém

### Estrutura Padrão (Verificada)

Cada US possui:
- [x] **Título**: US-XXX — Descrição
- [x] **Story Format**: Como/Quero/Para
- [x] **Critérios de Aceite**: Em formato Gherkin (Cenário/Dado/Quando/Então)
- ✅ **Observações**: Detalhes técnicos

**Exemplo (US-001):**
```
# US-001 — Catálogo de Roteiros Dinâmicos
Como: Arquivista
Quero: cadastrar e versionar roteiros
Para: identificar séries documentais

Critérios:
  Cenário 1: Criar roteiro com ramificação por LGPD
  Cenário 2: Versionamento com justificativa

Observações:
  - Editor com autosave
  - Validações de obrigatoriedade
```

---

## 🎯 Status de Completude

| Aspecto | Status | Detalhes |
|--------|--------|----------|
| **Existência de Arquivos** | ✅ 100% | Todos os 26 arquivos existem |
| **Conteúdo Mínimo** | ✅ 100% | Cada US tem critérios de aceite |
| **Formato Standard** | ✅ 100% | Gherkin/Story Format |
| **Rastreabilidade** | ✅ 100% | Por épico e numeração sequencial |
| **Links/Dependências** | ⚠️ Parcial | Requer revisão manual |
| **Estimativas (Story Points)** | ❌ Não | Pendente Planning Poker |
| **Priorização** | ❌ Não | Pendente Product Owner |

---

## ⏭️ Próxima Etapa Operacional (Interna)

**Matriz de apoio para execução de frontend:** `docs/hu/MATRIZ_PRIORIZACAO_FRONTEND_HW1.md`
**Plano de sprint enxuto (todas as US):** `docs/hu/PLANO_SPRINT_ENXUTO_TODAS_US.md`
**Quebra operacional B/F/QA (todas as US):** `docs/hu/PLANO_OPERACIONAL_TODAS_US_BFQ.md`
**Checklist diário (S1 a S5):** `docs/hu/CHECKLIST_DIARIO_SPRINTS_S1_A_S5.md`

### 1️⃣ Execução imediata do backlog núcleo
- Iniciar EP1 e EP2 como trilha prioritária.
- Tratar dependências críticas já mapeadas (US-002 → US-004; US-010 → US-020).

### 2️⃣ Refinamento objetivo (sem burocracia)
- Definir Story Points e prioridade somente para o próximo ciclo de execução.
- Manter detalhamento em tasks curtas, com responsável e critério de aceite.

### 3️⃣ Diretriz de frontend obrigatória
- Toda nova interface deve seguir identidade visual HW1 (tokens, componentes e contraste consistente).
- Evitar classes de cor hardcoded fora do design system.

### 4️⃣ Governança de acompanhamento enxuta
- Atualização por board interno + changelog curto por sprint.
- Sem necessidade de relatório detalhado de entrega externa.

---

## 📝 Conclusão

**✅ Histórias atualizadas e prontas para execução interna.**

- **26/26 US** com conteúdo base e critérios de aceite.
- **26/26 US** com seção de observações incluindo diretriz de identidade visual HW1 (quando houver interface).
- Escopo operacional ajustado para gestão interna (sem pacote formal de entrega).
- Sprint 1 do núcleo EP1 já foi implementada e validada tecnicamente (US-001 + fatia inicial de US-002).
- Sprint 2 já foi iniciada com o executor step-by-step de entrevistas apoiado no simulador condicional.
- Builder visual de condições (US-002) já foi implementado no frontend.
- Fluxo inicial de evidências/anexos (US-003) já está funcional com upload, hash e listagem.
- Integração com antivírus (ClamAV) já foi implementada no upload de evidências.
- Preview avançado de anexos já foi implementado (prévia local e preview remoto autenticado).
- Sprint 2 pode ser considerada concluída para o escopo previsto de US-002/US-003.
- Sprint 3 já foi iniciada com sugestão automática inicial de classe documental (US-004).
- Frontend do PCD (US-010) já foi iniciado com árvore hierárquica e cadastro básico de níveis.
- Operações avançadas do PCD foram evoluídas com edição de nível, criação/lista/aprovação de versões e diff visual (US-011).
- US-012 foi operacionalizada com configuração de metadados obrigatórios por classe, permissões por papel e validação de payload no módulo PCD.
- Módulos TTD, Ciclo de Vida e Governança foram operacionalizados no frontend com ações reais de API (US-020/021/022, US-030/US-031, US-040/041).
- US-022 foi implementada no TTD com criação/listagem de ordens, dupla aprovação, assinatura de termo com hash e teste de integração dedicado.
- US-030 foi implementada no Ciclo de Vida com agendamento de janelas, execução/reprocessamento idempotente e trilha de logs operacionais em hash encadeado.
- US-032 foi implementada no Ciclo de Vida com geração de selo de evidência (hash + timestamp + usuário + razão) e API de pacote de auditoria em JSON.
- US-050 foi iniciada com hardening da camada REST já existente: middleware global de rate limit para `/api/v1` e validação automática de bloqueio por excesso (429).
- US-051 foi iniciada com eventos internos assinados no ciclo de vida, incluindo disparo automático em aprovação, disparo manual e retry operacional.
- US-052 foi implementada com API de importação CSV, mapeamento de colunas, validação de erros/sucessos e dashboard operacional de importações.
- US-060 foi implementada com política RBAC/ABAC por sigilo, papel e unidade no PCD, incluindo validação de acesso do usuário autenticado.
- US-061 foi implementada com proteção LGPD em administração, criptografia em repouso, masking e anonimização de usuários.
- US-070 foi implementada com middleware de observabilidade, resumo de métricas/SLOs e dashboard principal alimentado por telemetria operacional.
- US-071 foi implementada com snapshots incrementais, listagem de backups e restauração parcial por classe/regra, além de painel administrativo operacional.
- US-080 foi implementada com inventário de qualidade sobre acervo importado, score de completude/unicidade/conformidade, regras de cleansing e histórico comparativo antes/depois.
- US-081 foi implementada com planner de ondas, dependências por unidade/processo, validação de prontidão e rollback operacional por fase.
- US-091 foi implementada com base de conhecimento, download de templates/guias e trilhas de onboarding com badge interno por progresso.
- US-090 foi implementada com prévia assistida da entrevista, barra de progresso, resumo de respostas e sugestão conjunta de PCD/TTD com justificativas.
- Testes de integração dos módulos EP1–EP10 permanecem verdes e a suíte backend cobre US-050, US-051, US-052, US-060, US-061, US-070, US-071, US-080, US-081, US-090 e US-091.
- Sprint 15 foi validada com smoke check operacional consolidado em `/health/smoke`, cobrindo PCD, TTD, ciclo de vida, governança, integração, dados/migração, conhecimento, observabilidade e backup.
- Painel de administração recebeu execução e leitura dos checks de smoke, com retorno por módulo para apoio à entrada em operação interna.
- Suíte E2E Playwright foi expandida e validada com fluxos críticos de login/dashboard, administração (smoke check), entrevistas (dry-run), PCD (validação de metadados) e TTD (revogação de hold).
- Bootstrap operacional do ambiente foi saneado com criação de `app.tasks`, migration inicial Alembic e correção de compatibilidade `passlib`/`bcrypt`, restaurando cadastro e login reais.
- Baseline de testes de carga e segurança da Sprint 15 foi reexecutada no backend com `k6`, `Locust` e `OWASP ZAP` baseline via Docker.
- Evidências coletadas: `Locust` com 270 requisições/0 falhas em 30s; `k6` com 2577 requisições/0 falhas em 2 minutos (`p95` global 18,63 ms; `/health/smoke` 29,1 ms); `ZAP` com 0 achados altos, 0 médios e apenas warnings residuais não bloqueantes em `/docs`.
- Suíte crítica do backend foi reestabilizada com correção estrutural do pytest para resolução do pacote `app`, mantendo 17 testes de módulos verdes na rodada atual.
- Runbook operacional interno consolidado em `docs/RUNBOOK_OPERACAO_INTERNA_S15.md` para repetição padronizada do ciclo.
- Sprint 16 (hardening incremental) iniciou com renovação de sessão via refresh token: endpoint `POST /api/v1/auth/refresh` implementado no backend e interceptor do frontend atualizado para retry automático com fila única de refresh em cenário de múltiplos `401`.
- Layout base do frontend recebeu melhorias de acessibilidade com skip link global, landmarks semânticos (`banner`, `main`, `nav`) e atributos `aria-*` em ações críticas de navegação/cabeçalho.
- Validação técnica da rodada incremental concluída em 12/03/2026: backend `20 passed` (`tests/test_auth_api.py` + `tests/test_modulos_api.py`), frontend `npm run lint` e `npm run build` verdes, Playwright `5/5` cenários críticos aprovados.
- Próximo passo: tratar melhorias incrementais de acessibilidade/performance como otimização contínua, sem bloquear a operação interna já validada.

---

> **Atualização de Status:** 12/03/2026  
> **Backlog HW1 — Gestão de Apoio Arquivístico**
