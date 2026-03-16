# Testes Não Funcionais — Sprint 15

## Escopo

- Carga baseline com `k6`.
- Carga baseline com `Locust`.
- Segurança baseline com `OWASP ZAP` (modo baseline via Docker).

## Variáveis de ambiente opcionais

- `BASE_URL` (default: `http://localhost:8000`)
- `AUTH_USERNAME`
- `AUTH_PASSWORD`
- `ACCESS_TOKEN`
- `ZAP_TARGET_URL`

Se `ACCESS_TOKEN` for informado, os cenários autenticados usam esse token.

Se `ACCESS_TOKEN` não for informado e `AUTH_USERNAME` + `AUTH_PASSWORD` estiverem disponíveis, os cenários tentam autenticação em `/api/v1/auth/login`.

## Execução

## Rodada validada (12/03/2026)

- `Locust` autenticado: 270 requisições, 0 falhas, 10 usuários, 30 segundos.
- `k6`: 2577 requisições, 0 falhas, `p95` global 18,63 ms, `p95` do smoke autenticado 29,1 ms.
- `OWASP ZAP`: relatório em `reports/zap-baseline-20260312-150142.md` com 0 alertas altos, 0 médios e apenas warnings residuais não bloqueantes após hardening HTTP e Swagger local.

### k6

```bash
make load-k6 AUTH_USERNAME=ops-sprint15@example.com AUTH_PASSWORD=Sprint15!Ops
```

### Locust (headless)

```bash
make load-locust AUTH_USERNAME=ops-sprint15@example.com AUTH_PASSWORD=Sprint15!Ops
```

### Execução direta no Windows (sem make)

```powershell
docker compose exec -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -e BASE_URL=http://localhost:8000 backend locust -f tests/nonfunctional/locustfile.py --headless -u 10 -r 2 -t 30s --host=http://localhost:8000
$scripts = (Resolve-Path '.\backend\tests\nonfunctional').Path
docker run --rm -i -e BASE_URL=http://host.docker.internal:8000 -e AUTH_USERNAME=ops-sprint15@example.com -e AUTH_PASSWORD=Sprint15!Ops -v "${scripts}:/scripts" grafana/k6 run /scripts/k6_smoke.js
```

### OWASP ZAP baseline (Windows / PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File backend/tests/nonfunctional/run_zap_baseline.ps1 -TargetUrl http://host.docker.internal:8000/docs -MaxMinutes 2
```

Relatórios do ZAP são gerados em `backend/tests/nonfunctional/reports/`.