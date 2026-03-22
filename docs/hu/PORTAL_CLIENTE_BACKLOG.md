# Portal do Cliente — Backlog Técnico de Sprint

**Projeto:** Gestão de Apoio Arquivístico  
**Data:** 21/03/2026  
**Objetivo:** Expor exclusivamente o módulo de Entrevistas a clientes externos (entrevistados), mantendo isolamento total dos módulos internos.  
**Modelo:** Intake Portal — o cliente responde e anexa; o arquivista controla o roteiro e analisa.

---

## Arquitetura Alvo (Resumo)

```
┌──────────────────────────────┐    ┌──────────────────────────────┐
│   DASHBOARD INTERNO          │    │   PORTAL DO CLIENTE          │
│   /dashboard/*               │    │   /portal/*                  │
│                              │    │                              │
│  roles: admin, gestor,       │    │  role: cliente               │
│         arquivista,          │    │                              │
│         classificador,       │    │  Entrevistas atribuídas      │
│         auditor, viewer      │    │  Respostas + Evidências      │
│                              │    │  Status (somente leitura)    │
│  Todos os módulos            │    │  Download do Laudo (futuro)  │
└──────┬───────────────────────┘    └──────┬───────────────────────┘
       │                                   │
       └──────────┬────────────────────────┘
                  ▼
         ┌─────────────────┐
         │  FastAPI Backend │
         │  /api/v1/*       │
         │                  │
         │  JWT + role gate │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │   PostgreSQL     │
         │   MinIO / S3     │
         └─────────────────┘
```

---

## Novo Papel: `cliente`

| Campo           | Valor                                                  |
|-----------------|--------------------------------------------------------|
| `role`          | `"cliente"`                                            |
| Visibilidade    | Apenas entrevistas onde `entrevistador_id == user.id`  |
| Escrita         | `respostas` e `evidências` de entrevistas `em_andamento` |
| Leitura extra   | Roteiro da entrevista (perguntas, condições) — somente leitura |
| Proibido        | TTD, PCD, Governança, Admin, Ciclo de Vida, Integração, Conhecimento, Dados/Migração |

---

## Máquina de Estados — Entrevista (visão do cliente)

```
              Arquivista cria
                   │
                   ▼
            ┌─────────────┐
            │ em_andamento │◄───── Cliente reabre (se permitido)
            └──────┬──────┘
                   │  Cliente submete
                   ▼
            ┌─────────────┐
            │  submetida   │  ← NOVO estado
            └──────┬──────┘
                   │  Arquivista revisa
                   ├────────────────────┐
                   ▼                    ▼
            ┌─────────────┐     ┌──────────────┐
            │  concluida   │     │  devolvida   │  ← NOVO estado
            └─────────────┘     └──────┬───────┘
                                       │  Cliente corrige
                                       ▼
                                ┌─────────────┐
                                │ em_andamento │
                                └─────────────┘
```

**Novos status:** `submetida`, `devolvida`  
**Regras:**
- Cliente só pode editar entrevistas `em_andamento` ou `devolvida`.
- Cliente transiciona para `submetida` ao terminar.
- Apenas roles internos (`arquivista`, `gestor`, `admin`) transitam para `concluida`, `devolvida` ou `cancelada`.
- `devolvida` inclui campo `motivo_devolucao` (texto obrigatório).

---

## Épicos e User Stories

### EP-CLI — Portal do Cliente

---

### FASE 1 — Backend: Papel `cliente` + Endpoints Restritos

#### US-CLI-01 — Papel `cliente` e controle de acesso

**Persona:** Administrador  
**Prioridade:** MUST

> Como Administrador, quero criar usuários com role `cliente` e garantir que eles não acessem módulos internos, para manter o isolamento de dados.

**Critérios de Aceitação:**

| # | Critério | Artefato |
|---|----------|----------|
| 1 | `role` aceita valor `"cliente"` na criação e edição de usuário | `admin.py` |
| 2 | `require_internal()` dependency rejeita `role == "cliente"` com HTTP 403 | `auth.py` (novo) |
| 3 | Todos os routers internos (ttd, pcd, governanca, ciclo_vida, integracao, conhecimento, dados_migracao, admin) usam `Depends(require_internal)` | Cada router |
| 4 | Test: cliente tenta `GET /ttd/regras` → 403 | `tests/` |
| 5 | Test: cliente tenta `GET /admin/usuarios` → 403 | `tests/` |

**Implementação:**

```python
# backend/app/routers/auth.py — nova dependency
INTERNAL_ROLES = {"admin", "gestor", "arquivista", "classificador", "auditor", "viewer"}

async def require_internal(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in INTERNAL_ROLES:
        raise HTTPException(403, "Acesso restrito a usuários internos")
    return current_user
```

---

#### US-CLI-02 — Novos status de entrevista (`submetida`, `devolvida`)

**Persona:** Arquivista / Cliente  
**Prioridade:** MUST

> Como Arquivista, quero que o cliente submeta a entrevista e eu possa devolver com motivo, para criar um fluxo de revisão antes de concluir.

**Critérios de Aceitação:**

| # | Critério | Artefato |
|---|----------|----------|
| 1 | Coluna `Entrevista.status` aceita `submetida` e `devolvida` | `roteiro.py` (model) |
| 2 | Novo campo `Entrevista.motivo_devolucao: str | None` (Text, nullable) | `roteiro.py` + migration |
| 3 | Novo campo `Entrevista.cliente_id: uuid | None` (FK users) — quem responde | `roteiro.py` + migration |
| 4 | Validação de transição de estados (ver matriz abaixo) | `roteiros.py` (router) |
| 5 | `motivo_devolucao` obrigatório quando `status → devolvida` | `roteiros.py` |
| 6 | Test: transição `em_andamento → submetida` OK | `tests/` |
| 7 | Test: transição `submetida → devolvida` com motivo OK | `tests/` |
| 8 | Test: transição `submetida → devolvida` sem motivo → 422 | `tests/` |

**Matriz de Transições Permitidas:**

| De \ Para         | em_andamento | submetida | concluida | devolvida | cancelada |
|-------------------|:---:|:---:|:---:|:---:|:---:|
| **em_andamento**  | —   | C   | I   | —   | I   |
| **submetida**     | —   | —   | I   | I   | I   |
| **devolvida**     | C   | C   | —   | —   | I   |
| **concluida**     | —   | —   | —   | —   | —   |
| **cancelada**     | —   | —   | —   | —   | —   |

> **C** = Cliente pode executar · **I** = Interno (arquivista/gestor/admin) pode executar

**Migration Alembic:**

```python
# alembic/versions/xxxx_add_entrevista_cliente_fields.py
def upgrade():
    op.add_column("entrevistas", sa.Column("cliente_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("entrevistas", sa.Column("motivo_devolucao", sa.Text(), nullable=True))
    # status já é varchar; os novos valores são apenas dados
```

---

#### US-CLI-03 — Endpoints do Portal do Cliente (backend)

**Persona:** Cliente  
**Prioridade:** MUST

> Como Cliente, quero acessar apenas as entrevistas atribuídas a mim, responder, anexar evidências e submeter, sem ver dados de outros módulos.

**Novos Endpoints — Prefixo `/api/v1/portal`:**

| Método | Path | Descrição | Response |
|--------|------|-----------|----------|
| `GET` | `/portal/entrevistas` | Lista entrevistas onde `cliente_id == current_user.id` | `list[EntrevistaClienteResponse]` |
| `GET` | `/portal/entrevistas/{id}` | Detalhe com roteiro + perguntas (read-only) | `EntrevistaClienteDetalhe` |
| `PATCH` | `/portal/entrevistas/{id}` | Atualizar `respostas` (só se `em_andamento` ou `devolvida`) | `EntrevistaClienteResponse` |
| `POST` | `/portal/entrevistas/{id}/submeter` | Transicionar para `submetida` | `EntrevistaClienteResponse` |
| `GET` | `/portal/entrevistas/{id}/evidencias` | Listar evidências da entrevista | `list[EvidenciaResponse]` |
| `POST` | `/portal/entrevistas/{id}/evidencias` | Upload de evidência (mesmas validações) | `EvidenciaResponse` |
| `DELETE` | `/portal/entrevistas/{id}/evidencias/{eid}` | Excluir evidência (só se `em_andamento` ou `devolvida`) | 204 |
| `GET` | `/portal/entrevistas/{id}/evidencias/{eid}/download` | Download de evidência própria | StreamingResponse |

**Schemas Novos:**

```python
class EntrevistaClienteResponse(BaseModel):
    id: uuid.UUID
    roteiro_titulo: str
    roteiro_area: str | None
    status: str
    respostas: dict
    motivo_devolucao: str | None
    created_at: datetime
    completed_at: datetime | None

class EntrevistaClienteDetalhe(EntrevistaClienteResponse):
    perguntas: list[PerguntaResponse]
    condicoes: list[CondicaoResponse]
    evidencias: list[EvidenciaResponse]
```

**Dependency de Segurança:**

```python
async def require_cliente(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "cliente":
        raise HTTPException(403, "Endpoint exclusivo para clientes")
    return current_user

async def get_entrevista_do_cliente(
    entrevista_id: uuid.UUID,
    current_user: User = Depends(require_cliente),
    db: AsyncSession = Depends(get_db),
) -> Entrevista:
    stmt = select(Entrevista).where(
        Entrevista.id == entrevista_id,
        Entrevista.cliente_id == current_user.id,
    )
    entrevista = (await db.execute(stmt)).scalar_one_or_none()
    if not entrevista:
        raise HTTPException(404, "Entrevista não encontrada")
    return entrevista
```

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | `GET /portal/entrevistas` retorna apenas entrevistas do cliente autenticado |
| 2 | `GET /portal/entrevistas` com outro usuário retorna lista vazia (sem vazamento) |
| 3 | `PATCH` com status `concluida` → 403 (cliente não pode concluir) |
| 4 | `PATCH` com entrevista `submetida` → 403 (cliente não pode editar depois de submeter) |
| 5 | `POST /submeter` valida que todas as perguntas obrigatórias foram respondidas |
| 6 | Upload de evidência respeita ClamAV + tamanho máximo |
| 7 | Download serve apenas evidências da entrevista do próprio cliente |
| 8 | Endpoints internos (`/roteiros/*`) continuam inacessíveis ao cliente |

---

#### US-CLI-04 — Atribuir entrevista a cliente (backend interno)

**Persona:** Arquivista  
**Prioridade:** MUST

> Como Arquivista, quero atribuir uma entrevista a um cliente específico ao criá-la, para que ele receba a tarefa no seu portal.

**Critérios de Aceitação:**

| # | Critério | Artefato |
|---|----------|----------|
| 1 | `POST /roteiros/{id}/entrevistas` aceita `cliente_id` opcional no body | `roteiros.py` |
| 2 | Se `cliente_id` informado, valida que o user existe e tem `role == "cliente"` | `roteiros.py` |
| 3 | `GET /roteiros/{id}/entrevistas` retorna `cliente_id` e `cliente_nome` | `roteiros.py` |
| 4 | `PATCH /roteiros/entrevistas/{id}` aceita `cliente_id` (reatribuir) — apenas roles internos | `roteiros.py` |
| 5 | Test: atribuir entrevista a user não-cliente → 422 | `tests/` |

**Schema atualizado:**

```python
class EntrevistaCreateRequest(BaseModel):
    respostas: dict = {}
    cliente_id: uuid.UUID | None = None  # ← novo

class EntrevistaUpdateRequest(BaseModel):
    respostas: dict | None = None
    status: str | None = None
    cliente_id: uuid.UUID | None = None  # ← novo (só internos)
    motivo_devolucao: str | None = None  # ← novo (só internos)
```

---

### FASE 2 — Frontend: Portal do Cliente

#### US-CLI-05 — Layout e roteamento do Portal

**Persona:** Cliente  
**Prioridade:** MUST

> Como Cliente, quero acessar um portal visual limpo, sem sidebar de módulos internos, para focar apenas nas minhas entrevistas.

**Critérios de Aceitação:**

| # | Critério | Artefato |
|---|----------|----------|
| 1 | Nova rota `/portal` com `layout.tsx` dedicado (sem AppSidebar) | `frontend/src/app/portal/layout.tsx` |
| 2 | Header simplificado: logo HW1 + nome do cliente + botão Sair | `frontend/src/components/layout/portal-header.tsx` |
| 3 | `middleware.ts` redireciona `role == "cliente"` de `/dashboard/*` para `/portal` | `frontend/middleware.ts` |
| 4 | `middleware.ts` redireciona roles internos de `/portal/*` para `/dashboard` | `frontend/middleware.ts` |
| 5 | Login detecta role e redireciona automaticamente para a área correta | `frontend/src/app/login/page.tsx` |

**Estrutura de Pastas:**

```
frontend/src/app/
├── portal/
│   ├── layout.tsx              ← layout limpo (sem sidebar)
│   ├── page.tsx                ← lista de entrevistas do cliente
│   └── entrevistas/
│       └── [id]/
│           └── page.tsx        ← detalhe/resposta da entrevista
├── dashboard/                  ← existente (internos)
│   └── ...
```

---

#### US-CLI-06 — Página de listagem de entrevistas (cliente)

**Persona:** Cliente  
**Prioridade:** MUST

> Como Cliente, quero ver a lista das entrevistas atribuídas a mim com status visual, para saber o que preciso responder.

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | Tabela/cards com colunas: Roteiro (título), Área, Status, Criada em, Ações |
| 2 | Badge de status com cores: `em_andamento` (amarelo), `submetida` (azul), `devolvida` (vermelho), `concluida` (verde) |
| 3 | Botão "Responder" visível apenas se `em_andamento` ou `devolvida` |
| 4 | Botão "Ver" para entrevistas `submetida` ou `concluida` (somente leitura) |
| 5 | Mensagem de devolução exibida em destaque quando `devolvida` |
| 6 | Estado vazio ("Nenhuma entrevista atribuída") quando lista vazia |
| 7 | Chamada: `GET /portal/entrevistas` |

---

#### US-CLI-07 — Página de resposta de entrevista (cliente)

**Persona:** Cliente  
**Prioridade:** MUST

> Como Cliente, quero responder as perguntas do roteiro passo a passo (wizard), anexar evidências e submeter, para cumprir minha parte no processo arquivístico.

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | Wizard step-by-step reutiliza lógica de condições/simulação existente |
| 2 | Cada pergunta renderiza input por tipo (texto, número, select, multi_select, boolean) |
| 3 | Seções agrupam perguntas (quando `secao` definida) |
| 4 | Auto-save a cada mudança de step (`PATCH /portal/entrevistas/{id}`) |
| 5 | Painel lateral de evidências por pergunta (upload/delete/preview) |
| 6 | Barra de progresso (preenchidas / obrigatórias) |
| 7 | Botão "Submeter" validando obrigatórias → `POST /portal/entrevistas/{id}/submeter` |
| 8 | Confirmação antes de submeter ("Após submeter, você não poderá editar até uma eventual devolução") |
| 9 | Se `devolvida`: banner com `motivo_devolucao` no topo da página |
| 10 | Se `submetida` ou `concluida`: formulário em modo somente leitura |

---

#### US-CLI-08 — Atribuir entrevista a cliente (frontend interno)

**Persona:** Arquivista  
**Prioridade:** MUST

> Como Arquivista, quero escolher o cliente ao criar ou editar uma entrevista, para que ele receba a tarefa.

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | No form de criar entrevista: combobox "Cliente" busca users com `role == "cliente"` |
| 2 | Endpoint auxiliar: `GET /admin/usuarios?role=cliente` (já existe com filtro) ou novo `GET /portal/clientes` simplificado |
| 3 | Na listagem de entrevistas (interno): coluna "Cliente" com nome |
| 4 | Na edição de entrevista (interno): possibilidade de reatribuir |
| 5 | Validação: não permite atribuir a user inativo |

---

### FASE 3 — Pacote de Entrega (pós-MVP)

#### US-CLI-09 — Laudo / Pacote de Entrega

**Persona:** Arquivista / Cliente  
**Prioridade:** SHOULD (pós-MVP)

> Como Arquivista, quero gerar um laudo PDF com as respostas, evidências e classificação sugerida, para entregar ao cliente como documento formal.

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | `POST /roteiros/entrevistas/{id}/laudo` gera PDF via Celery task |
| 2 | PDF contém: dados do roteiro, perguntas/respostas, evidências (thumbnails), PCD sugerida, justificativa |
| 3 | PDF assinado com hash SHA-256 para integridade |
| 4 | `GET /portal/entrevistas/{id}/laudo` permite download pelo cliente (só se `concluida`) |
| 5 | Laudo armazenado no MinIO com retenção |

---

#### US-CLI-10 — Notificações por e-mail

**Persona:** Cliente / Arquivista  
**Prioridade:** COULD (pós-MVP)

> Como Cliente, quero receber e-mail quando uma entrevista for atribuída ou devolvida, para não precisar checar o portal manualmente.

**Critérios de Aceitação:**

| # | Critério |
|---|----------|
| 1 | E-mail ao cliente quando entrevista é atribuída (com link direto) |
| 2 | E-mail ao cliente quando entrevista é devolvida (com motivo) |
| 3 | E-mail ao arquivista quando cliente submete entrevista |
| 4 | Templates HTML com identidade HW1 |
| 5 | Celery task assíncrona para envio (SMTP configurável) |

---

## Estimativa de Esforço por Story

| US | Título | Backend | Frontend | Testes | Total est. |
|----|--------|:-------:|:--------:|:------:|:----------:|
| CLI-01 | Papel `cliente` + ACL | M | — | P | **M** |
| CLI-02 | Novos status (submetida/devolvida) | M | — | M | **M** |
| CLI-03 | Endpoints portal (8 endpoints) | G | — | G | **G** |
| CLI-04 | Atribuir entrevista a cliente | P | — | P | **P** |
| CLI-05 | Layout e roteamento portal | — | M | — | **M** |
| CLI-06 | Listagem entrevistas (cliente) | — | M | — | **M** |
| CLI-07 | Página resposta wizard (cliente) | — | G | — | **G** |
| CLI-08 | Atribuir no frontend (interno) | — | M | — | **M** |
| CLI-09 | Laudo PDF | G | P | M | **G** |
| CLI-10 | Notificações e-mail | M | — | P | **M** |

> **P** = Pequeno (< 2h) · **M** = Médio (2–4h) · **G** = Grande (4–8h)

---

## Ordem de Execução Recomendada (Sprint Plan)

### Sprint N — Fundação (Backend)

| Ordem | US | Dependência |
|:-----:|-----|------------|
| 1 | CLI-01 | — |
| 2 | CLI-02 | CLI-01 |
| 3 | CLI-04 | CLI-02 |
| 4 | CLI-03 | CLI-02, CLI-04 |

**Entrega:** Backend completo; testável via Swagger/curl.

### Sprint N+1 — Portal (Frontend)

| Ordem | US | Dependência |
|:-----:|-----|------------|
| 5 | CLI-05 | CLI-03 |
| 6 | CLI-06 | CLI-05 |
| 7 | CLI-07 | CLI-06 |
| 8 | CLI-08 | CLI-04 |

**Entrega:** Portal funcional end-to-end.

### Sprint N+2 — Maturação (pós-MVP)

| Ordem | US | Dependência |
|:-----:|-----|------------|
| 9 | CLI-09 | CLI-03 |
| 10 | CLI-10 | CLI-03 |

**Entrega:** Entrega formal com laudo + alertas proativos.

---

## Checklist de Segurança e LGPD

- [ ] Filtro `cliente_id == current_user.id` aplicado em TODAS as queries do portal (row-level)
- [ ] Nenhum endpoint do portal expõe IDs de outros clientes ou dados internos
- [ ] Upload de evidência mantém ClamAV scan + limite de tamanho
- [ ] Download de evidência valida propriedade antes de servir blob
- [ ] Logs de auditoria registram ações do cliente (quem, quando, o quê)
- [ ] Senha do cliente segue mesma política de hash (bcrypt/argon2)
- [ ] Token JWT do cliente tem mesma expiração e refresh policy
- [ ] CORS permite origem do portal (se domínio separado no futuro)
- [ ] Rate limiting nos endpoints de upload para evitar abuso
- [ ] `motivo_devolucao` sanitizado contra XSS antes de renderizar no frontend
