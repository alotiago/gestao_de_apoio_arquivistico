# Ambiente Local - Gestão de Apoio Arquivístico

Guia prático para evolução e operação do ambiente local.

## Objetivos

- Subir o projeto rapidamente para desenvolvimento.
- Garantir validação simples de status e saúde.
- Padronizar comandos para todo o time.

## Pré-requisitos

- Docker Desktop
- Make (Linux/WSL/Git Bash)
- Python 3.12+
- Node.js 20+

## Bootstrap rápido

```bash
git clone <repo-url>
cd gestao_de_apoio_arquivistico
make dev-init
```

O `dev-init` faz:

- cria `.env` a partir de `.env.example` se necessário;
- sobe a stack local;
- aplica migrations no backend.

## Operação diária

```bash
make dev-up       # sobe toda a stack
make dev-infra    # sobe somente infra base
make dev-status   # lista serviços e portas
make dev-health   # valida endpoint /health do backend
make logs         # logs agregados
make backend-logs # logs do backend
make frontend-logs
```

## Fluxo de backend local sem Docker (opcional)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Fluxo de frontend local sem Docker (opcional)

```bash
cd frontend
npm install
npm run dev
```

## Diagnóstico rápido

1. Se `make dev-health` falhar, rode `make backend-logs`.
2. Se o backend não conectar no banco, confira `DATABASE_URL` no `.env`.
3. Se Celery falhar, valide Redis com `make redis-cli`.
4. Se autenticação falhar após redeploy, preserve segredos no `.env` e evite regenerar senha de Postgres sem `ALTER USER`.
