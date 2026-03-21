#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico}"
REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"
ENABLE_UFW="${ENABLE_UFW:-true}"

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

if [ "${EUID}" -ne 0 ]; then
  echo "Execute como root (sudo)."
  exit 1
fi

log "Instalando dependencias base"
apt-get update -y
apt-get install -y ca-certificates curl git ufw

if ! command -v docker >/dev/null 2>&1; then
  log "Instalando Docker Engine"
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  log "Instalando plugin docker compose"
  apt-get install -y docker-compose-plugin
fi

# Permite usar docker sem sudo para o usuario de login
if [ -n "${SUDO_USER:-}" ]; then
  usermod -aG docker "${SUDO_USER}" || true
fi

if [ -d "${APP_DIR}/.git" ]; then
  log "Repositorio ja existe. Atualizando branch ${BRANCH}"
  git -C "${APP_DIR}" fetch --all --prune
  git -C "${APP_DIR}" checkout "${BRANCH}"
  git -C "${APP_DIR}" pull --ff-only origin "${BRANCH}"
else
  if [ -z "${REPO_URL}" ]; then
    echo "REPO_URL obrigatorio na primeira execucao."
    echo "Exemplo: sudo REPO_URL=https://github.com/ORG/gestao_de_apoio_arquivistico.git ./deploy/oci/deploy_vm.sh"
    exit 1
  fi

  log "Clonando repositorio"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"

if [ ! -f .env ]; then
  log "Criando .env inicial a partir de .env.oci.example"
  cp .env.oci.example .env
  echo "Arquivo .env criado. Ajuste os secrets antes de subir em producao."
fi

if grep -q "SEU_IP_OU_DOMINIO\|CHANGE_ME_" .env; then
  echo "Detectado placeholder no .env. Edite o arquivo antes do deploy: ${APP_DIR}/.env"
  exit 1
fi

if [ "${ENABLE_UFW}" = "true" ]; then
  log "Configurando firewall (UFW): 22, 80, 443"
  ufw allow OpenSSH || true
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
  ufw --force enable || true
fi

log "Subindo stack OCI com build de imagens"
docker compose -f docker-compose.oci.yml up -d --build

log "Aplicando migrations"
docker compose -f docker-compose.oci.yml exec -T backend alembic upgrade head

log "Aguardando healthcheck via Nginx"
for i in $(seq 1 40); do
  if curl -fsS http://localhost/health >/dev/null; then
    break
  fi
  sleep 3
  if [ "$i" -eq 40 ]; then
    echo "Timeout aguardando /health. Verifique logs: docker compose -f docker-compose.oci.yml logs --tail=200"
    exit 1
  fi
done

log "Deploy concluido"
echo "Frontend: http://<IP_PUBLICO>/"
echo "Backend health: http://<IP_PUBLICO>/health"
echo "API docs: http://<IP_PUBLICO>/docs"
echo "Comando de logs: docker compose -f docker-compose.oci.yml logs -f"
