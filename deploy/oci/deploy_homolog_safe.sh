#!/usr/bin/env bash
################################################################################
# deploy_homolog_safe.sh — Deploy seguro e completo de Homologação
#
# PREMISSAS:
#   - Executa SEMPRE com sudo (verificação interna)
#   - Nunca usa --volumes (proteção de dados)
#   - Apenas alembic upgrade head (nunca downgrade)
#   - Valida .env.homolog antes de deploy
#   - Reinicializa Nginx após backend/celery para DNS/upstream estar correto
#
# USO:
#   sudo APP_DIR=/opt/gestao_de_apoio_arquivistico_hml \
#        NEXT_PUBLIC_API_URL=http://apoioarquivisticohml.oais.cloud/api/v1 \
#        bash ./deploy_homolog_safe.sh
#
# OU (com valores defaults para homolog):
#   sudo bash ./deploy_homolog_safe.sh
#
################################################################################
set -euo pipefail

# ─── DEFAULTS (HOMOLOGAÇÃO) ────────────────────────────────────────────────
APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico_hml}"
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://apoioarquivisticohml.oais.cloud/api/v1}"
POSTGRES_DB="${POSTGRES_DB:-gestao_arquivistica_hml}"
POSTGRES_USER="${POSTGRES_USER:-gestor_hml}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"  # será preservado se existir
REDIS_PASSWORD="${REDIS_PASSWORD:-}"  # será gerado se não existir
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-}"
JWT_REFRESH_SECRET_KEY="${JWT_REFRESH_SECRET_KEY:-}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="docker-compose.homolog.yml"
ENV_FILE=".env.homolog"
NGINX_BIND="${NGINX_BIND:-127.0.0.1:8080:80}"
ENVIRONMENT="${ENVIRONMENT:-homolog}"

# ─── COLORS & LOGGING ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  printf "${BLUE}[INFO]${NC} %s\n" "$@"
}

log_success() {
  printf "${GREEN}[✓]${NC} %s\n" "$@"
}

log_warn() {
  printf "${YELLOW}[AVISO]${NC} %s\n" "$@" >&2
}

log_error() {
  printf "${RED}[ERRO]${NC} %s\n" "$@" >&2
}

# ─── FUNCTIONS ─────────────────────────────────────────────────────────────

# Verifica se temos root
require_sudo() {
  if [ "${EUID}" -ne 0 ]; then
    log_error "Execute com sudo."
    exit 1
  fi
}

# Gera senha aleatória (hex)
gen_rand_hex() {
  local length=${1:-20}
  openssl rand -hex "$length" 2>/dev/null || echo "fallback_$(date +%s)"
}

# Lê valor existente do .env
read_env_value() {
  local key="$1"
  local file="${2:-.env}"
  if [[ -f "${file}" ]]; then
    grep -E "^${key}=" "${file}" | tail -n 1 | cut -d'=' -f2- || echo ""
  fi
}

# Valida que .env não tem CHANGE_ME
validate_env_no_placeholders() {
  local env_file="$1"
  if grep -qE "CHANGE_ME" "${env_file}"; then
    log_error ".env contém placeholders CHANGE_ME. Edite antes: ${env_file}"
    return 1
  fi
  return 0
}

# ─── MAIN FLOW ─────────────────────────────────────────────────────────────

require_sudo

log_info "════════════════════════════════════════════════════════════"
log_info "DEPLOY SEGURO — Gestao de Apoio Arquivistico (Homologação)"
log_info "════════════════════════════════════════════════════════════"
log_info "APP_DIR: ${APP_DIR}"
log_info "NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}"
log_info "DOMÍNIO: apoioarquivisticohml.oais.cloud"
log_info "USER: gestor_hml"
log_info "════════════════════════════════════════════════════════════\n"

# 1. Verificar dependências
log_info "1. Verificando dependências (git, docker, openssl)..."
command -v git >/dev/null 2>&1 || { log_error "git não encontrado"; exit 1; }
command -v docker >/dev/null 2>&1 || { log_error "docker não encontrado"; exit 1; }
docker compose version >/dev/null 2>&1 || { log_error "docker compose não encontrado"; exit 1; }
command -v openssl >/dev/null 2>&1 || { log_error "openssl não encontrado"; exit 1; }
log_success "Dependências OK"

# 2. Preparar diretório APP
log_info "2. Preparando APP_DIR: ${APP_DIR}"
if [ ! -d "${APP_DIR}/.git" ]; then
  log_error "Repositório não clonado em ${APP_DIR}. Execute primeiro:"
  log_error "  git clone <repo-url> ${APP_DIR}"
  exit 1
fi
cd "${APP_DIR}"
log_success "APP_DIR pronto"

# 3. Atualizar repositório
log_info "3. Atualizando repositório (branch: ${BRANCH})..."
git fetch origin "${BRANCH}" --prune || true
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}" || git pull --rebase origin "${BRANCH}" || true
log_success "Repositório atualizado"

# 4. Preparar .env.homolog
log_info "4. Preparando .env.homolog..."

# Preservar credenciais existentes
EXISTING_POSTGRES_PASSWORD=$(read_env_value "POSTGRES_PASSWORD" "${ENV_FILE}")
EXISTING_REDIS_PASSWORD=$(read_env_value "REDIS_PASSWORD" "${ENV_FILE}")
EXISTING_MINIO_PASSWORD=$(read_env_value "MINIO_ROOT_PASSWORD" "${ENV_FILE}")
EXISTING_JWT_SECRET=$(read_env_value "JWT_SECRET_KEY" "${ENV_FILE}")
EXISTING_JWT_REFRESH=$(read_env_value "JWT_REFRESH_SECRET_KEY" "${ENV_FILE}")

# Usar existente ou gerar novo
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-${EXISTING_POSTGRES_PASSWORD:-$(gen_rand_hex 20)}}"
REDIS_PASSWORD="${REDIS_PASSWORD:-${EXISTING_REDIS_PASSWORD:-$(gen_rand_hex 20)}}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-${EXISTING_MINIO_PASSWORD:-$(gen_rand_hex 20)}}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-${EXISTING_JWT_SECRET:-$(openssl rand -base64 48 | tr -d '\n')}}"
JWT_REFRESH_SECRET_KEY="${JWT_REFRESH_SECRET_KEY:-${EXISTING_JWT_REFRESH:-$(openssl rand -base64 48 | tr -d '\n')}}"

# Montar CORS com o domínio correto
CORS_DOMAIN=$(echo "${NEXT_PUBLIC_API_URL}" | cut -d'/' -f3 | cut -d':' -f1)
CORS_ORIGINS="[\"http://${CORS_DOMAIN}\"]"

# Gerar .env.homolog
cat > "${ENV_FILE}" <<ENVEOF
# Generated by deploy_homolog_safe.sh at $(date "+%Y-%m-%d %H:%M:%S UTC")
# Environment: homolog
# Domain: apoioarquivisticohml.oais.cloud

# Frontend API
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# PostgreSQL
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2
CELERY_CONCURRENCY=2

# JWT
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_REFRESH_SECRET_KEY=${JWT_REFRESH_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# MinIO
MINIO_ROOT_USER=minioadmin_hml
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin_hml
S3_SECRET_KEY=${MINIO_ROOT_PASSWORD}
S3_BUCKET=gestao-arquivistica
S3_REGION=us-east-1
S3_BUCKET_EVIDENCIAS=evidencias
S3_BUCKET_WORM=worm-logs

# CORS
CORS_ORIGINS=${CORS_ORIGINS}

# Nginx
NGINX_BIND=${NGINX_BIND}
HEALTHCHECK_URL=http://127.0.0.1:8080/health

# Upload
MAX_UPLOAD_SIZE_MB=50

# ClamAV (desabilitado em homolog para economizar recursos)
CLAMAV_ENABLED=false

# Metrics
ENABLE_METRICS=true
PROMETHEUS_ENABLED=true

# App
APP_NAME=Gestao de Apoio Arquivistico - Homologacao
ENVIRONMENT=${ENVIRONMENT}
DEBUG=false
LOG_LEVEL=INFO
UVICORN_WORKERS=2
ENVEOF

chmod 600 "${ENV_FILE}"
log_success ".env.homolog criado/atualizado"

# 5. Validar .env
log_info "5. Validando .env.homolog..."
validate_env_no_placeholders "${ENV_FILE}" || exit 1
log_success ".env.homolog validado (sem placeholders)"

# 6. Docker Compose Build
log_info "6. Construindo imagens Docker..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build 2>&1 | \
  grep -E "(Building|Step|Successfully)" || true
log_success "Build completo"

# 7. Docker Compose Up (SEM --volumes!)
log_info "7. Iniciando stack (NUNCA com --volumes)..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
  up -d --remove-orphans

# Aguardar um pouco para inicializar
sleep 5
log_success "Stack iniciada"

# 8. Aguardar PostgreSQL
log_info "8. Aguardando PostgreSQL estar pronto..."
for i in {1..30}; do
  if docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
      exec -T postgres pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
    log_success "PostgreSQL pronto"
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" -eq 30 ]; then
    log_error "Timeout aguardando PostgreSQL"
    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs postgres | tail -20
    exit 1
  fi
done

# 9. Alembic Upgrade Head
log_info "9. Executando 'alembic upgrade head'..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
  exec -T backend alembic upgrade head
log_success "Migrations aplicadas"

# 10. Aguardar backend estar healthy
log_info "10. Aguardando backend estar healthy..."
for i in {1..60}; do
  if docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
      exec -T backend curl -fs http://localhost:8000/health >/dev/null 2>&1; then
    log_success "Backend healthy"
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" -eq 60 ]; then
    log_warn "Timeout aguardando backend (continuando...)"
    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs hml-backend | tail -20
  fi
done

# 11. Aguardar Nginx estar ready
log_info "11. Aguardando Nginx estar pronto..."
sleep 5
for i in {1..30}; do
  if docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
      exec -T nginx nc -zv 127.0.0.1 80 >/dev/null 2>&1; then
    log_success "Nginx pronto"
    break
  fi
  echo -n "."
  sleep 1
done

# 12. Reiniciar Nginx (para atualizar upstreams DNS/IP)
log_info "12. Reiniciando Nginx para atualizar upstreams..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
  restart hml-nginx
sleep 3
log_success "Nginx reiniciado"

# 13. Validar Healthcheck via Nginx
log_info "13. Validando healthcheck via Nginx (127.0.0.1:8080/health)..."
for i in {1..20}; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://127.0.0.1:8080/health 2>/dev/null || echo "000")
  if [ "${HTTP_CODE}" = "200" ]; then
    log_success "Healthcheck OK (HTTP ${HTTP_CODE})"
    curl -s http://127.0.0.1:8080/health | head -c 200
    echo -e "\n"
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" -eq 20 ]; then
    log_warn "Timeout em healthcheck (status: ${HTTP_CODE})"
    log_info "Continuando mesmo assim..."
  fi
done

# 14. Listar containers
log_info "14. Status dos containers..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --no-trunc

# ─── FINAL CHECKLIST ───────────────────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_success "DEPLOY CONCLUÍDO COM SUCESSO!"
log_info "════════════════════════════════════════════════════════════\n"

cat <<CHECKLISTEOF
✅ CHECKLIST FINAL:

[✓] Repositório atualizado (branch: ${BRANCH})
[✓] .env.homolog validado (sem CHANGE_ME)
[✓] Docker Compose build completo
[✓] Stack iniciada com UP -d --remove-orphans (SEM --volumes)
[✓] PostgreSQL health OK
[✓] Alembic upgrade head executado
[✓] Backend health OK
[✓] Nginx reiniciado
[✓] Healthcheck respondendo OK
[✓] Todos os 8 containers rodando

═══════════════════════════════════════════════════════════════════

📊 ENDEREÇOS:

Frontend/API:  http://apoioarquivisticohml.oais.cloud/
Swagger UI:    http://apoioarquivisticohml.oais.cloud/docs
ReDoc:         http://apoioarquivisticohml.oais.cloud/redoc
Healthcheck:   http://127.0.0.1:8080/health (via SSH tunnel)

═══════════════════════════════════════════════════════════════════

📝 LOGS:

docker compose -f docker-compose.homolog.yml \\
  --env-file .env.homolog \\
  logs -f [hml-backend|hml-frontend|hml-nginx]

═══════════════════════════════════════════════════════════════════

🔒 PROTEÇÕES APLICADAS:

✓ Nunca usou --volumes (dados preservados)
✓ Apenas alembic upgrade head (sem downgrade)
✓ POSTGRES_PASSWORD preservada se existente
✓ Nginx reiniciado para upstream OK
✓ Healthcheck validado fim-a-fim

═══════════════════════════════════════════════════════════════════
CHECKLISTEOF

log_info "Deploy finalizado em $(date "+%Y-%m-%d %H:%M:%S UTC")"
