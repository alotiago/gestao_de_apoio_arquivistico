# ===========================================================
# Makefile — Gestão de Apoio Arquivístico
# ===========================================================

.PHONY: help up down build logs backend-logs frontend-logs \
	migrate migrate-create db-reset test test-cov \
	load-k6 load-locust security-zap \
	lint format backend-shell psql redis-cli

help: ## Exibir esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Docker ----
up: ## Subir todos os containers (dev)
	docker compose up -d

down: ## Parar todos os containers
	docker compose down

build: ## Rebuild de todos os containers
	docker compose build --no-cache

logs: ## Ver logs de todos os serviços
	docker compose logs -f

backend-logs: ## Ver logs do backend
	docker compose logs -f backend

frontend-logs: ## Ver logs do frontend
	docker compose logs -f frontend

# ---- Database ----
migrate: ## Executar migrations pendentes
	docker compose exec backend alembic upgrade head

migrate-create: ## Criar nova migration (usage: make migrate-create MSG="descricao")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Resetar banco (drop + recreate + migrate)
	docker compose exec postgres psql -U gestor -d postgres -c "DROP DATABASE IF EXISTS gestao_arquivistica;"
	docker compose exec postgres psql -U gestor -d postgres -c "CREATE DATABASE gestao_arquivistica;"
	$(MAKE) migrate

# ---- Test ----
test: ## Rodar testes do backend
	docker compose exec backend pytest -v --tb=short

test-cov: ## Rodar testes com cobertura
	docker compose exec backend pytest --cov=app --cov-report=html --cov-report=term

load-k6: ## Rodar baseline de carga com k6
	docker run --rm -i \
		-e BASE_URL="$(or $(BASE_URL),http://host.docker.internal:8000)" \
		-e AUTH_USERNAME="$(AUTH_USERNAME)" \
		-e AUTH_PASSWORD="$(AUTH_PASSWORD)" \
		-e ACCESS_TOKEN="$(ACCESS_TOKEN)" \
		-v "$(CURDIR)/backend/tests/nonfunctional:/scripts" \
		grafana/k6 run /scripts/k6_smoke.js

load-locust: ## Rodar baseline de carga com Locust (headless)
	docker compose exec \
		-e BASE_URL="$(or $(BASE_URL),http://localhost:8000)" \
		-e AUTH_USERNAME="$(AUTH_USERNAME)" \
		-e AUTH_PASSWORD="$(AUTH_PASSWORD)" \
		-e ACCESS_TOKEN="$(ACCESS_TOKEN)" \
		backend locust -f tests/nonfunctional/locustfile.py --headless -u 10 -r 2 -t 2m --host=http://localhost:8000

security-zap: ## Rodar baseline de segurança OWASP ZAP (Docker)
	powershell -ExecutionPolicy Bypass -File backend/tests/nonfunctional/run_zap_baseline.ps1 -TargetUrl http://host.docker.internal:8000

# ---- Lint / Format ----
lint: ## Verificar lint do backend
	docker compose exec backend ruff check app/

format: ## Formatar código do backend
	docker compose exec backend ruff format app/

# ---- Shells ----
backend-shell: ## Abrir shell no container do backend
	docker compose exec backend bash

psql: ## Abrir psql no banco
	docker compose exec postgres psql -U gestor -d gestao_arquivistica

redis-cli: ## Abrir redis-cli
	docker compose exec redis redis-cli

# ---- Frontend ----
frontend-install: ## Instalar deps do frontend
	cd frontend && npm install

frontend-dev: ## Rodar frontend localmente (fora do Docker)
	cd frontend && npm run dev

frontend-lint: ## Lint do frontend
	cd frontend && npm run lint

# ---- Celery ----
celery-log: ## Ver logs do celery worker
	docker compose logs -f celery-worker
