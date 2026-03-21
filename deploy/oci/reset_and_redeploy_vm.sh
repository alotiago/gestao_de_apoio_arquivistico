#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico}"
REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"
APP_DOMAIN="${APP_DOMAIN:-}"
HOST_IP="${HOST_IP:-10.10.11.92}"
PUBLIC_SCHEME="${PUBLIC_SCHEME:-https}"
APP_ENVIRONMENT="${APP_ENVIRONMENT:-production}"
APP_NAME="${APP_NAME:-Gestao de Apoio Arquivistico}"
NGINX_BIND="${NGINX_BIND:-127.0.0.1:8080:80}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8080/health}"
PURGE_APP_DIR="${PURGE_APP_DIR:-false}"
ENABLE_UFW="${ENABLE_UFW:-true}"
KEEP_ENV_BACKUP="${KEEP_ENV_BACKUP:-true}"
ENV_BACKUP_DIR="${ENV_BACKUP_DIR:-/var/backups/gestao_de_apoio_arquivistico}"
ENV_BACKUP_PATH=""

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

fail() {
  echo "ERRO: $1" >&2
  exit 1
}

if [ "${EUID}" -ne 0 ]; then
  fail "Execute como root (sudo)."
fi

need() {
  command -v "$1" >/dev/null 2>&1 || fail "Comando ausente: $1"
}

need git
need docker
need curl

if [ -d "${APP_DIR}" ] && [ -f "${APP_DIR}/.env" ] && [ "${KEEP_ENV_BACKUP}" = "true" ]; then
  mkdir -p "${ENV_BACKUP_DIR}"
  ENV_BACKUP_PATH="${ENV_BACKUP_DIR}/.env.$(date '+%Y%m%d%H%M%S').backup"
  log "Salvando backup do .env em ${ENV_BACKUP_PATH}"
  cp "${APP_DIR}/.env" "${ENV_BACKUP_PATH}"
fi

if [ -d "${APP_DIR}" ] && [ -f "${APP_DIR}/docker-compose.oci.yml" ]; then
  log "Derrubando stack atual do GAA"
  cd "${APP_DIR}"
  docker compose -f docker-compose.oci.yml down -v --remove-orphans || true
fi

log "Removendo containers residuais do GAA"
for container in gaa-postgres gaa-redis gaa-minio gaa-clamav gaa-backend gaa-celery-worker gaa-celery-beat gaa-frontend gaa-nginx; do
  docker rm -f "$container" >/dev/null 2>&1 || true
done

log "Removendo imagens do GAA"
for image in gestao_de_apoio_arquivistico-backend gestao_de_apoio_arquivistico-frontend; do
  docker image rm -f "$image" >/dev/null 2>&1 || true
done

if [ "${PURGE_APP_DIR}" = "true" ]; then
  [ -n "${REPO_URL}" ] || fail "REPO_URL é obrigatório quando PURGE_APP_DIR=true."
  log "Apagando diretório da aplicação para recriação limpa"
  rm -rf "${APP_DIR}"
fi

if [ ! -d "${APP_DIR}/.git" ]; then
  [ -n "${REPO_URL}" ] || fail "REPO_URL é obrigatório na primeira execução ou após purge."
  log "Clonando repositório limpo em ${APP_DIR}"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
else
  log "Atualizando repositório para a branch ${BRANCH}"
  git -C "${APP_DIR}" fetch --all --prune
  git -C "${APP_DIR}" checkout "${BRANCH}"
  git -C "${APP_DIR}" pull --ff-only origin "${BRANCH}"
fi

cd "${APP_DIR}"

if [ -n "${ENV_BACKUP_PATH}" ] && [ -f "${ENV_BACKUP_PATH}" ] && [ ! -f .env ]; then
  log "Restaurando .env a partir do backup externo"
  cp "${ENV_BACKUP_PATH}" .env
  chmod 600 .env
fi

log "Gerando .env de produção"
APP_DIR="${APP_DIR}" \
HOST_IP="${HOST_IP}" \
APP_DOMAIN="${APP_DOMAIN}" \
PUBLIC_SCHEME="${PUBLIC_SCHEME}" \
APP_ENVIRONMENT="${APP_ENVIRONMENT}" \
APP_NAME="${APP_NAME}" \
NGINX_BIND="${NGINX_BIND}" \
./deploy/oci/remote_prepare_env.sh

if ! grep -q '^HEALTHCHECK_URL=' .env; then
  printf '\nHEALTHCHECK_URL=%s\n' "${HEALTHCHECK_URL}" >> .env
fi

log "Executando deploy limpo"
APP_DIR="${APP_DIR}" \
REPO_URL="${REPO_URL}" \
BRANCH="${BRANCH}" \
ENABLE_UFW="${ENABLE_UFW}" \
HEALTHCHECK_URL="${HEALTHCHECK_URL}" \
./deploy/oci/deploy_vm.sh

log "Validando health interno"
curl -fsS "${HEALTHCHECK_URL}" >/dev/null

echo
echo "Reset e redeploy concluídos."
echo "Health interno: ${HEALTHCHECK_URL}"
if [ -n "${APP_DOMAIN}" ]; then
  echo "Domínio público esperado: ${PUBLIC_SCHEME}://${APP_DOMAIN}/"
fi