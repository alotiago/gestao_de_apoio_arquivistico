# Gestão de Apoio Arquivístico

Sistema de gestão documental com entrevistas assistidas, Plano de Classificação (PCD), Tabela de Temporalidade (TTD) e execução do ciclo de vida, incluindo governança, segurança e integrações.

## 🏗️ Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI |
| Frontend | Node.js 20 + Next.js 14 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Task Queue | Celery + Redis |
| Storage | MinIO (S3-compatible) |
| Auth | Keycloak (OIDC) |

## 🚀 Quick Start

### Pré-requisitos
- Docker Desktop
- Python 3.12+
- Node.js 20 LTS
- Git

### Desenvolvimento Local

```bash
# 1. Clonar repositório
git clone <repo-url>
cd gestao_de_apoio_arquivistico

# 2. Subir infraestrutura (PostgreSQL, Redis, MinIO)
docker-compose up -d postgres redis minio

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Frontend (novo terminal)
cd frontend
npm install
npm run dev
```

### Com Docker Compose (tudo junto)

```bash
docker-compose up --build
```

**Acesso:**
- Frontend: http://localhost:4000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## 🛡️ Hardening Sprint 15 (Carga e Segurança)

Baseline não funcional adicionada em `backend/tests/nonfunctional`:

- `k6_smoke.js` para carga rápida de endpoints de saúde e smoke autenticado opcional.
- `locustfile.py` para carga controlada com usuários virtuais e login opcional.
- `run_zap_baseline.ps1` para auditoria OWASP ZAP baseline via Docker.

Rodada validada em 12/03/2026:

- `Locust`: 270 requisições em 30 segundos com 10 usuários, 0 falhas e smoke autenticado estável.
- `k6`: 2577 requisições em 2 minutos, 0 falhas, `p95` global de 18,63 ms e `p95` do `/health/smoke` de 29,1 ms.
- `OWASP ZAP`: baseline executada em `/docs`, com 0 achados altos, 0 médios e apenas warnings residuais não bloqueantes (`Non-Storable Content`, `Timestamp Disclosure - Unix` e `Modern Web Application`). Relatórios gerados em `backend/tests/nonfunctional/reports/`.

Execução rápida:

```bash
# Requer make (Linux/WSL/Git Bash)
make load-k6
make load-locust
make security-zap
```

```powershell
# Windows PowerShell (sem make)
docker compose exec -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -e BASE_URL=http://localhost:8000 backend locust -f tests/nonfunctional/locustfile.py --headless -u 10 -r 2 -t 30s --host=http://localhost:8000
$scripts = (Resolve-Path '.\backend\tests\nonfunctional').Path
docker run --rm -i -e BASE_URL=http://host.docker.internal:8000 -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -v "${scripts}:/scripts" grafana/k6 run /scripts/k6_smoke.js
powershell -ExecutionPolicy Bypass -File .\backend\tests\nonfunctional\run_zap_baseline.ps1 -TargetUrl http://host.docker.internal:8000/docs -MaxMinutes 2
```

## 📁 Estrutura do Projeto

```
gestao_de_apoio_arquivistico/
├── backend/           # Python / FastAPI
├── frontend/          # Node.js / Next.js 14
├── infrastructure/    # Docker, Nginx, Prometheus, Grafana
├── docs/              # Documentação e histórias de usuário
└── docker-compose.yml
```

## 📋 Documentação

- [Plano de Trabalho](docs/PLANO_DE_TRABALHO.md) — Sprints, estimativas, roadmap
- [Histórias de Usuários](docs/hu/HISTORIAS_USUARIOS_COMPLETO.md) — Backlog completo (26 US)
- [Backlog HW1](docs/hu/backlog-hw1-like/README.md) — Épicos, features, personas
- [Runbook Operação Interna S15](docs/RUNBOOK_OPERACAO_INTERNA_S15.md) — Guia de subida, validação, carga e segurança

## 📊 Status do Projeto

| Aspecto | Status |
|---------|--------|
| Backlog | ✅ 26 US definidas |
| Plano de Trabalho | ✅ 16 Sprints planejadas |
| Setup do Projeto | 🔄 Sprint 0 |
| MVP (EP1-EP4) | ⬜ Sprint 1-7 |
| Release 1.0 | ✅ Sprint 15 validada tecnicamente (12/03/2026) |

---

> **Projeto HW1** — Gestão de Apoio Arquivístico  
> **Licença:** Proprietário
