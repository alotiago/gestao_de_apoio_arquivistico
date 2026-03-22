# MVP de CRUD — Backlog Priorizado

**Projeto:** Gestão de Apoio Arquivístico  
**Data:** 21/03/2026  
**Objetivo:** Completar as operações CRUD mínimas para viabilizar cadastro e manutenção manual de dados em todos os módulos.  
**Referência:** Mapeamento de lacunas sobre os 12 routers e 10 páginas de dashboard existentes.

---

## Legenda de Prioridade (MoSCoW)

| Tag | Significado | Critério |
|-----|------------|----------|
| **MUST** | Obrigatório para MVP | Bloqueia uso operacional do módulo |
| **SHOULD** | Esperado no MVP | Módulo funciona, mas com atrito |
| **COULD** | Desejável pós-MVP | Melhoria de produtividade |
| **WONT** | Fora de escopo agora | Imutabilidade intencional ou baixo valor |

---

## Resumo de Gaps por Módulo

| # | Módulo | C | R | U | D | Prioridade |
|---|--------|---|---|---|---|------------|
| 1 | TTD — Regras de Retenção | ✅ | ✅ | ❌ | ❌ | MUST |
| 2 | Governança — Matriz | ✅ | ✅ | ❌ | ❌ | MUST |
| 3 | Dados/Migração — Regras Cleansing | ✅ | ✅ | ❌ | ❌ | MUST |
| 4 | Conhecimento — Templates e Trilhas | ❌ | ✅ | parcial | ❌ | MUST |
| 5 | Ciclo de Vida — Jobs/Selos | ✅ | ✅ | parcial | ❌ | SHOULD |
| 6 | Integração — Importações | ✅ | ✅ | ❌ | ❌ | SHOULD |
| 7 | Roteiros — Perguntas/Evidências | ✅ | ✅ | ✅ | ❌ | COULD |
| 8 | Dados/Migração — Ondas | ✅ | ✅ | ✅ | ❌ | COULD |
| 9 | Admin — Senha / Self-service | ✅ | ✅ | parcial | ✅ | SHOULD |

> PCD e Usuários já possuem CRUD completo e não entram neste backlog.  
> Audit Logs (Governança) e Versões (PCD/Roteiros) são imutáveis por design — WONT.

---

## P1 — MUST (Bloqueia uso operacional)

### US-101 — CRUD completo de Regras de Retenção (TTD)

**Épico:** EP3 — TTD  
**Complementa:** US-020  
**Persona:** Gestor de Documentos

> Como Gestor de Documentos, quero editar e excluir regras de retenção existentes, para corrigir prazos, bases legais e eventos sem precisar recriar a regra.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `PATCH /ttd/regras/{regra_id}` permite alterar `evento_inicio`, `prazo_dias`, `destinacao_final`, `base_legal` | ✅ criar | ✅ criar |
| 2 | `DELETE /ttd/regras/{regra_id}` com soft-delete (status → `inativa`); regras vinculadas a holds ativos não podem ser excluídas | ✅ criar | ✅ criar |
| 3 | `GET /ttd/regras/{regra_id}` retorna regra individual (falta endpoint de leitura individual) | ✅ criar | — |
| 4 | Tabela de regras no frontend exibe botões Editar/Excluir por linha | — | ✅ criar |
| 5 | Modal/form de edição pré-carrega valores atuais e valida campos obrigatórios | — | ✅ criar |
| 6 | Confirmação antes de exclusão ("Tem certeza? Esta ação marcará a regra como inativa") | — | ✅ criar |
| 7 | Regras inativas ficam ocultas por padrão; toggle "Mostrar inativas" na listagem | — | ✅ criar |

---

### US-102 — CRUD completo da Matriz de Rastreabilidade (Governança)

**Épico:** EP5 — Governança  
**Complementa:** US-040  
**Persona:** Compliance Officer

> Como Compliance Officer, quero editar e excluir entradas da matriz legislação ↔ série, para manter a rastreabilidade atualizada quando a legislação muda.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `PATCH /governanca/matriz/{entrada_id}` permite alterar `legislacao`, `artigo`, `norma_interna`, `risco`, `evidencia` | ✅ criar | ✅ criar |
| 2 | `DELETE /governanca/matriz/{entrada_id}` com soft-delete (status → `revogada`) | ✅ criar | ✅ criar |
| 3 | Cada alteração/exclusão gera registro automático no audit log (hashchain) | ✅ criar | — |
| 4 | Tabela de entradas exibe ações Editar/Excluir | — | ✅ criar |
| 5 | Form de edição valida que `pcd_nivel_id` referenciado existe e está ativo | ✅ criar | ✅ criar |
| 6 | Entradas revogadas visíveis com filtro; padrão mostra apenas ativas | — | ✅ criar |

---

### US-103 — CRUD completo de Regras de Cleansing (Dados/Migração)

**Épico:** EP9 — Dados e Migração  
**Complementa:** US-080  
**Persona:** Master Data Manager

> Como Master Data Manager, quero editar e excluir regras de cleansing, para ajustar transformações quando os dados ou requisitos mudam.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `PATCH /dados-migracao/regras-cleansing/{regra_id}` permite alterar `nome`, `tipo`, `campo`, `configuracao`, `ativo` | ✅ criar | ✅ criar |
| 2 | `DELETE /dados-migracao/regras-cleansing/{regra_id}` com soft-delete (ativo → false) | ✅ criar | ✅ criar |
| 3 | `GET /dados-migracao/regras-cleansing/{regra_id}` retorna regra individual | ✅ criar | — |
| 4 | Tabela de regras exibe ações Editar/Desativar por linha | — | ✅ criar |
| 5 | Form de edição pré-carrega campos e exibe preview da transformação (sample in → sample out) | — | ✅ criar |
| 6 | Não é possível excluir regra referenciada por inventário ativo; exibe aviso | ✅ criar | ✅ criar |

---

### US-104 — CRUD de Templates e Trilhas de Conhecimento

**Épico:** EP10 — UX e Adoção  
**Complementa:** US-091  
**Persona:** Gestor de Adoção

> Como Gestor de Adoção, quero cadastrar, editar e excluir templates e trilhas de onboarding via interface, em vez de depender de dados hardcoded no código.

**Critérios de Aceitação — Templates:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | Modelo `Template` persistido em banco (migrar dados do `knowledge_base_store` in-memory para tabela) | ✅ criar | — |
| 2 | `POST /conhecimento/templates` cria template (titulo, slug, descricao, conteudo_md, tags, tipo) | ✅ criar | ✅ criar |
| 3 | `PATCH /conhecimento/templates/{slug}` atualiza campos | ✅ criar | ✅ criar |
| 4 | `DELETE /conhecimento/templates/{slug}` com soft-delete | ✅ criar | ✅ criar |
| 5 | Página de conhecimento ganha aba "Gerenciar Templates" com tabela + form (somente role admin/gestor) | — | ✅ criar |

**Critérios de Aceitação — Trilhas:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 6 | Modelo `Trilha` persistido em banco (migrar `onboarding_trilhas` in-memory) | ✅ criar | — |
| 7 | `POST /conhecimento/trilhas` cria trilha (titulo, descricao, perfil_alvo, etapas[]) | ✅ criar | ✅ criar |
| 8 | `PATCH /conhecimento/trilhas/{trilha_id}` atualiza campos e etapas | ✅ criar | ✅ criar |
| 9 | `DELETE /conhecimento/trilhas/{trilha_id}` com soft-delete | ✅ criar | ✅ criar |
| 10 | Seção "Gerenciar Trilhas" com editor de etapas (drag-and-drop para reordenar) | — | ✅ criar |

---

## P2 — SHOULD (Módulo funciona, mas com atrito)

### US-105 — Exclusão de Jobs de Retenção e Selos (Ciclo de Vida)

**Épico:** EP4 — Ciclo de Vida  
**Complementa:** US-030, US-032  
**Persona:** Arquivista

> Como Arquivista, quero cancelar jobs agendados por engano e excluir selos de evidência inválidos, para manter a fila de processamento limpa.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `PATCH /ciclo-vida/jobs/{job_id}/cancelar` muda status para `cancelado` (somente jobs `agendado`) | ✅ criar | ✅ criar |
| 2 | `DELETE /ciclo-vida/jobs/{job_id}` com soft-delete; jobs `executado` não podem ser excluídos | ✅ criar | ✅ criar |
| 3 | `DELETE /ciclo-vida/selos/{selo_id}` permitido apenas se selo está em status `rascunho`; selos finalizados são imutáveis | ✅ criar | ✅ criar |
| 4 | Botão "Cancelar" visível em jobs agendados; botão "Excluir" com confirmação | — | ✅ criar |

---

### US-106 — Reprocessar / Excluir Importações (Integração)

**Épico:** EP6 — Integração  
**Complementa:** US-052  
**Persona:** Admin

> Como Admin, quero reprocessar uma importação com erros ou excluir importações orphaned, para manter o histórico de integrações limpo.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `POST /integracao/importacoes/{importacao_id}/reprocessar` re-executa o parse com o mesmo arquivo e mapping | ✅ criar | ✅ criar |
| 2 | `DELETE /integracao/importacoes/{importacao_id}` com soft-delete (status → `excluida`); só se não gerou registros com vínculo externo | ✅ criar | ✅ criar |
| 3 | Botão "Reprocessar" visível em importações com status `erro`; botão "Excluir" com confirmação | — | ✅ criar |
| 4 | Reprocessamento gera novo registro de resultados (mantém histórico anterior) | ✅ | — |

---

### US-107 — Alteração de Senha e Self-service (Admin)

**Épico:** EP7 — Segurança  
**Complementa:** US-060  
**Persona:** Usuário autenticado

> Como Usuário autenticado, quero alterar minha senha pelo painel, e como Admin quero resetar senha de outro usuário, para reduzir dependência de suporte.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `PATCH /auth/me/senha` recebe `senha_atual` + `nova_senha`; valida força mínima (8 chars, 1 maiúscula, 1 número) | ✅ criar | ✅ criar |
| 2 | `POST /admin/usuarios/{user_id}/reset-senha` gera senha temporária e retorna ao Admin; força troca no próximo login | ✅ criar | ✅ criar |
| 3 | Página de perfil (`/dashboard/perfil` ou modal) com form "Alterar Senha" | — | ✅ criar |
| 4 | Botão "Reset Senha" na tabela de usuários (admin) com confirmação | — | ✅ criar |
| 5 | Hash bcrypt com cost ≥ 12; senha antiga nunca trafega em log | ✅ | — |

---

## P3 — COULD (Desejável pós-MVP)

### US-108 — Excluir Perguntas e Evidências de Roteiros

**Épico:** EP1 — Entrevistas  
**Complementa:** US-001, US-003  
**Persona:** Arquivista

> Como Arquivista, quero excluir perguntas individuais e arquivos de evidência de uma entrevista, para corrigir erros sem recriar o roteiro inteiro.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `DELETE /roteiros/{roteiro_id}/perguntas/{pergunta_id}` remove pergunta e suas condições | ✅ criar | ✅ criar |
| 2 | `DELETE /roteiros/evidencias/{evidencia_id}` remove arquivo do storage (MinIO) e registro | ✅ criar | ✅ criar |
| 3 | Impedir exclusão de pergunta se há entrevistas `em_andamento` que a referenciam | ✅ criar | — |
| 4 | Ícone de lixeira por pergunta/evidência com confirmação | — | ✅ criar |

---

### US-109 — Leitura Individual e Exclusão de Ondas de Migração

**Épico:** EP9 — Dados e Migração  
**Complementa:** US-081  
**Persona:** Migration Manager

> Como Migration Manager, quero visualizar detalhes de uma onda específica e excluir ondas em planejamento, para gerenciar o cronograma de migração.

**Critérios de Aceitação:**

| # | Critério | Backend | Frontend |
|---|----------|---------|----------|
| 1 | `GET /dados-migracao/ondas/{onda_id}` retorna onda com fases e dependências | ✅ criar | ✅ criar |
| 2 | `DELETE /dados-migracao/ondas/{onda_id}` permitido apenas para ondas `planejada` | ✅ criar | ✅ criar |
| 3 | Navegar para tela de detalhe da onda ao clicar na linha da tabela | — | ✅ criar |
| 4 | Botão "Excluir" visível apenas em ondas `planejada` | — | ✅ criar |

---

## P4 — WONT (Imutável por design / baixo valor agora)

| Item | Módulo | Justificativa |
|------|--------|---------------|
| Excluir Audit Logs | Governança | Imutabilidade WORM é requisito (US-041) |
| Excluir Versões de PCD | PCD | Snapshots são provas de rastreabilidade |
| Excluir Versões de Roteiro | Entrevistas | Histórico de versionamento não deve ser apagado |
| Editar holds encerrados | TTD | Hold encerrado é registro legal |
| Editar ordens assinadas | TTD | Assinatura digital torna imutável |
| CRUD completo de Workflows | Ciclo de Vida | Workflows são gerados automaticamente pelo motor |

---

## Ordem de Execução Sugerida

```
Sprint N   ─── US-101 (TTD Regras)      ── MUST
           ─── US-102 (Governança)       ── MUST

Sprint N+1 ─── US-103 (Cleansing)       ── MUST
           ─── US-104 (Conhecimento)     ── MUST

Sprint N+2 ─── US-107 (Senha/Self-svc)  ── SHOULD
           ─── US-105 (Jobs/Selos)       ── SHOULD

Sprint N+3 ─── US-106 (Importações)     ── SHOULD
           ─── US-108 (Perguntas/Evid.)  ── COULD
           ─── US-109 (Ondas detalhe)    ── COULD
```

**Critério de ordenação:**
1. MUST primeiro — desbloqueiam cadastro operacional
2. Dentro de MUST: TTD e Governança antes (são dependência de compliance)
3. SHOULD: agrupados por sprint para reduzir context-switch
4. COULD: encaixados quando sobrar capacity

---

## Estimativa de Esforço (T-shirt)

| US | Backend | Frontend | Total |
|----|---------|----------|-------|
| US-101 | S | S | **S** |
| US-102 | S | S | **S** |
| US-103 | S | S | **S** |
| US-104 | M | M | **M** |
| US-105 | S | S | **S** |
| US-106 | M | S | **M** |
| US-107 | M | M | **M** |
| US-108 | S | S | **S** |
| US-109 | S | S | **S** |

> S = < 1 dia | M = 1–2 dias | L = 3+ dias

---

## Rastreabilidade com Backlog Existente

| Nova US | Complementa | Épico |
|---------|-------------|-------|
| US-101 | US-020 | EP3 |
| US-102 | US-040 | EP5 |
| US-103 | US-080 | EP9 |
| US-104 | US-091 | EP10 |
| US-105 | US-030, US-032 | EP4 |
| US-106 | US-052 | EP6 |
| US-107 | US-060 | EP7 |
| US-108 | US-001, US-003 | EP1 |
| US-109 | US-081 | EP9 |
