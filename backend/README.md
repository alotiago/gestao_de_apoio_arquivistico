# Backend — Gestão de Apoio Arquivístico (FastAPI)

## Estrutura

```
app/
├── main.py            # FastAPI app entry point
├── config.py          # Settings (env vars)
├── database.py        # SQLAlchemy engine + session
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic schemas (request/response)
├── routers/           # API route handlers
├── services/          # Business logic layer
├── tasks/             # Celery async tasks
├── middleware/         # Auth, RBAC, audit
└── utils/             # Helpers (crypto, storage, conarq)
```

## Setup Local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Testes

```bash
pytest --cov=app --cov-report=html
```

## API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
