# Runbook Operação Interna — Sprint 15

## 1) Pré-requisitos

- Docker Desktop ativo.
- `docker compose` disponível no terminal.
- Porta `8000` livre para backend.

## 2) Subida do ambiente

```powershell
cd c:\des\gestao_de_apoio_arquivistico
docker compose up -d postgres redis minio clamav backend celery-worker celery-beat
```

## 3) Bootstrap de banco

```powershell
cd c:\des\gestao_de_apoio_arquivistico
docker compose exec backend alembic upgrade head
```

## 4) Validação operacional mínima

### 4.1 Health público

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8000/health' | ConvertTo-Json
```

### 4.2 Login + Smoke autenticado

```powershell
$token = (Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/api/v1/auth/login' -ContentType 'application/x-www-form-urlencoded' -Body 'username=ops-sprint15%40example.com&password=Sprint15!Ops').access_token
Invoke-RestMethod -Method Get -Uri 'http://localhost:8000/health/smoke' -Headers @{ Authorization = "Bearer $token" } | ConvertTo-Json
```

Critério de aceite: `overall_status = "ok"` e `failed_checks = []`.

## 5) Carga e segurança (baseline)

### 5.1 Locust (carga curta)

```powershell
docker compose exec -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -e BASE_URL=http://localhost:8000 backend locust -f tests/nonfunctional/locustfile.py --headless -u 10 -r 2 -t 30s --host=http://localhost:8000
```

### 5.2 k6 (carga controlada)

```powershell
$scripts = (Resolve-Path '.\backend\tests\nonfunctional').Path
docker run --rm -i -e BASE_URL=http://host.docker.internal:8000 -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -v "${scripts}:/scripts" grafana/k6 run /scripts/k6_smoke.js
```

### 5.3 OWASP ZAP baseline

```powershell
powershell -ExecutionPolicy Bypass -File .\backend\tests\nonfunctional\run_zap_baseline.ps1 -TargetUrl http://host.docker.internal:8000/docs -MaxMinutes 2
```

Relatórios: `backend/tests/nonfunctional/reports/`.

## 6) Troubleshooting rápido

- **Celery reiniciando em loop:** validar módulo `app.tasks` e refazer build do backend/worker/beat.
- **Login falhando 401/500:** confirmar migration (`alembic upgrade head`) e existência da tabela `users`.
- **ZAP com warnings:** tratar como não bloqueante quando `exit code = 2` (relatórios ainda são gerados).

## 7) Encerramento

```powershell
docker compose down
```
