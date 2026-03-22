#!/usr/bin/env bash
# ===========================================================
# deploy_homolog.sh — Deploy seguro no ambiente de HOMOLOGACAO
#
# GARANTIA PRINCIPAL: nunca usa --volumes nem apaga dados.
# Apenas "alembic upgrade head" é executado — nunca downgrade.
#
# PRIMEIRO USO (VM zerada):
#   1. Execute remote_prepare_env_hml.sh para gerar .env.homolog
#   2. Execute este script
#
# USO NORMAL (atualizações):
#   sudo APP_DIR=/opt/gestao_de_apoio_arquivistico_hml ./deploy/oci/deploy_homolog.sh
#
# JAMAIS use --volumes: isso apagaria irreversivelmente o banco
# de homologação (postgres_data_hml).
# ===========================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico_hml}"
REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"
ENABLE_UFW="${ENABLE_UFW:-false}"
COMPOSE_FILE="docker-compose.homolog.yml"
ENV_FILE=".env.homolog"
ENV_EXAMPLE=".env.homolog.example"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8080/health}"

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

warn() {
  printf '\n[AVISO] %s\n' "$1" >&2
}

# ─── root check ───────────────────────────────────────────-
if [ "${EUID}" -ne 0 ]; then
  echo "Execute como root (sudo)."
  exit 1
fi

# ─── dependências base ────────────────────────────────────
log "Verificando dependencias (git, docker, curl)"
apt-get update -y -qq
apt-get install -y -qq ca-certificates curl git

if ! command -v docker >/dev/null 2>&1; then
  log "Instalando Docker Engine"
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  log "Instalando plugin docker compose"
  apt-get install -y -qq docker-compose-plugin
fi

if [ -n "${SUDO_USER:-}" ]; then
  usermod -aG docker "${SUDO_USER}" || true
fi

# ─── firewall (opcional, por segurança não abre porta 80) ─
if [ "${ENABLE_UFW}" = "true" ]; then
  log "Configurando UFW (22 apenas — porta 8080 fica behind SSH tunnel)"
  ufw allow OpenSSH || true
  ufw --force enable || true
fi

# ─── repositório ──────────────────────────────────────────
if [ -d "${APP_DIR}/.git" ]; then
  log "Atualizando branch ${BRANCH} em ${APP_DIR}"
  git -C "${APP_DIR}" fetch --all --prune
  git -C "${APP_DIR}" checkout "${BRANCH}"
  git -C "${APP_DIR}" pull --ff-only origin "${BRANCH}"
else
  if [ -z "${REPO_URL}" ]; then
    echo "REPO_URL obrigatorio na primeira execucao."
    echo "Exemplo: sudo REPO_URL=https://github.com/ORG/gestao_de_apoio_arquivistico.git ./deploy_homolog.sh"
    exit 1
  fi
  log "Clonando repositorio em ${APP_DIR}"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"

# ─── .env.homolog ─────────────────────────────────────────
if [ ! -f "${ENV_FILE}" ]; then
  if [ -f "${ENV_EXAMPLE}" ]; then
    log "Criando ${ENV_FILE} a partir de ${ENV_EXAMPLE}"
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    warn "${ENV_FILE} criado com placeholders CHANGE_ME. Edite antes de continuar:"
    warn "  nano ${APP_DIR}/${ENV_FILE}"
    echo ""
    echo "Reexecute o script apos editar ${ENV_FILE}."
    exit 0
  else
    echo "Arquivo ${ENV_FILE} nao encontrado e ${ENV_EXAMPLE} tambem nao existe."
    echo "Execute primeiro: ${APP_DIR}/deploy/oci/remote_prepare_env_hml.sh"
    exit 1
  fi
fi

# Bloqueia deploy com placeholders nao preenchidos
if grep -qE "CHANGE_ME" "${ENV_FILE}"; then
  echo "Detectados placeholders CHANGE_ME em ${ENV_FILE}."
  echo "Edite o arquivo antes do deploy: ${APP_DIR}/${ENV_FILE}"
  exit 1
fi

# ─── build das imagens ────────────────────────────────────
log "Construindo imagens (gaa-backend:homolog, gaa-frontend:homolog)"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build

# ─── subir stack — SEM --volumes ──────────────────────────
log "Subindo stack de homologacao (NUNCA com --volumes)"
# A linha abaixo é PROPOSITALMENTE sem --volumes.
# --volumes apagaria postgres_data_hml e todos os dados de homologacao.
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans

# ─── migrations — apenas upgrade head ─────────────────────
log "Aguardando banco estar pronto"
for i in $(seq 1 20); do
  if docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
      exec -T postgres pg_isready -U "${POSTGRES_USER:-gestor_hml}" >/dev/null 2>&1; then
    break
  fi
  sleep 3
  if [ "$i" -eq 20 ]; then
    echo "Timeout aguardando PostgreSQL."
    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=50 postgres
    exit 1
  fi
done

log "Aplicando migrations (alembic upgrade head)"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" \
  exec -T backend alembic upgrade head

# ─── healthcheck ──────────────────────────────────────────
log "Aguardando healthcheck em ${HEALTHCHECK_URL}"
for i in $(seq 1 40); do
  if curl -fsS "${HEALTHCHECK_URL}" >/dev/null 2>&1; then
    break
  fi
  sleep 3
  if [ "$i" -eq 40 ]; then
    echo "Timeout aguardando healthcheck em ${HEALTHCHECK_URL}."
    echo "Verifique os logs: docker compose -f ${COMPOSE_FILE} logs --tail=100"
    exit 1
  fi
done

# ─── resumo ───────────────────────────────────────────────
log "Deploy de homologacao concluido"
echo ""
echo "  Acesso (via SSH tunnel):"
echo "    ssh -L 8080:127.0.0.1:8080 <usuario>@<IP_VM>"
echo "    Abrir: http://localhost:8080"
echo ""
echo "  MinIO console (via SSH tunnel):"
echo "    ssh -L 9091:127.0.0.1:9091 <usuario>@<IP_VM>"
echo "    Abrir: http://localhost:9091"
echo ""
echo "  Logs: docker compose -f ${COMPOSE_FILE} logs -f"
echo "  Status: docker compose -f ${COMPOSE_FILE} ps"
echo ""
warn "JAMAIS execute --volumes em homolog — isso apaga o banco postgres_data_hml."
warn "Para atualizar sem recriar dados: execute este script novamente."
