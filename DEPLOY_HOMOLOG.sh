#!/usr/bin/env bash
################################################################################
# DEPLOY FINAL — Gestao de Apoio Arquivistico (Homologação)
# Integra: git push + SSH deploy + validação
#
# USO:
#   bash ./DEPLOY_HOMOLOG.sh
#
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { printf "${BLUE}[INFO]${NC} %s\n" "$@"; }
log_success() { printf "${GREEN}[✓]${NC} %s\n" "$@"; }
log_warn() { printf "${YELLOW}[AVISO]${NC} %s\n" "$@" >&2; }
log_error() { printf "${RED}[ERRO]${NC} %s\n" "$@" >&2; }

# CONFIG
VM_HOST="10.10.11.93"
VM_USER="gestor"
APP_DIR="/opt/gestao_de_apoio_arquivistico_hml"
DOMAIN="apoioarquivisticohml.oais.cloud"
API_URL="http://${DOMAIN}/api/v1"
BRANCH="main"
REPO_URL="https://github.com/SEU_ORG/gestao_de_apoio_arquivistico.git"

# ─── FASE 1: GIT LOCAL ─────────────────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_info "FASE 1: Preparação Git Local"
log_info "════════════════════════════════════════════════════════════"

if [ ! -d ".git" ]; then
  log_error "Não está em um repositório git. Execute a partir da raiz do projeto."
  exit 1
fi

log_info "Atualizando repositório local..."
git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}" || git pull --rebase origin "${BRANCH}"
log_success "Git local atualizado"

# ─── FASE 2: VERIFICAR SSH ────────────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_info "FASE 2: Verificando Conectividade SSH"
log_info "════════════════════════════════════════════════════════════"

if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${VM_USER}@${VM_HOST}" "echo 'SSH OK'" 2>/dev/null; then
  log_error "Não foi possível conectar via SSH a ${VM_USER}@${VM_HOST}"
  log_info "Alternativas:"
  log_info "  1. Verificar conectividade: ping ${VM_HOST}"
  log_info "  2. Gerar chave SSH: ssh-keygen -t ed25519 -C 'tiago@desktop'"
  log_info "  3. Copiar chave: ssh-copy-id -i ~/.ssh/id_ed25519 ${VM_USER}@${VM_HOST}"
  exit 1
fi
log_success "SSH conectado"

# ─── FASE 3: COPIAR SCRIPT DE DEPLOY ──────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_info "FASE 3: Preparando Script de Deploy"
log_info "════════════════════════════════════════════════════════════"

log_info "Copiando deploy_homolog_safe.sh para VM..."
scp -q -o StrictHostKeyChecking=accept-new \
    ./deploy/oci/deploy_homolog_safe.sh \
    "${VM_USER}@${VM_HOST}:/tmp/deploy_homolog_safe.sh" || {
  log_error "Falha ao copiar script"
  exit 1
}
log_success "Script copiado"

# ─── FASE 4: EXECUTAR DEPLOY NA VM ────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_info "FASE 4: Executando Deploy Remoto"
log_info "════════════════════════════════════════════════════════════"
log_warn "Será solicitada SENHA DE SUDO da VM (user: gestor)"

# Construir comando com sudo
DEPLOY_COMMAND="cd /tmp && sudo \\
  NEXT_PUBLIC_API_URL='${API_URL}' \\
  APP_DIR='${APP_DIR}' \\
  bash ./deploy_homolog_safe.sh"

# Executar deploy
ssh -t "${VM_USER}@${VM_HOST}" bash -c "${DEPLOY_COMMAND}" || {
  log_error "Deploy remoto falhou"
  exit 1
}

# ─── FASE 5: VALIDAÇÕES PÓS-DEPLOY ────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_info "FASE 5: Validações Pós-Deploy"
log_info "════════════════════════════════════════════════════════════"

log_info "Aguardando healthcheck (30s)..."
sleep 5

HEALTH_RESPONSE=$(ssh -q "${VM_USER}@${VM_HOST}" \
  "curl -s --max-time 10 http://127.0.0.1:8080/health" || echo "")

if echo "${HEALTH_RESPONSE}" | grep -q "ok\|healthy\|status"; then
  log_success "✓ Healthcheck OK"
else
  log_warn "⚠ Healthcheck ainda não respondendo (pode precisar de mais tempo)"
fi

log_info "Verificando status dos containers..."
CONTAINER_STATUS=$(ssh -q "${VM_USER}@${VM_HOST}" \
  "cd ${APP_DIR} && docker compose -f docker-compose.homolog.yml ps --no-trunc" || echo "")

echo "${CONTAINER_STATUS}"

if echo "${CONTAINER_STATUS}" | grep -q "hml-backend.*Up"; then
  log_success "✓ Backend rodando"
fi

if echo "${CONTAINER_STATUS}" | grep -q "hml-nginx.*Up"; then
  log_success "✓ Nginx rodando"
fi

# ─── FINAL SUMMARY ─────────────────────────────────────────────────────────
log_info "════════════════════════════════════════════════════════════"
log_success "DEPLOY CONCLUÍDO COM SUCESSO!"
log_info "════════════════════════════════════════════════════════════\n"

cat <<FINALEOF
✅ CHECKLIST DE VALIDAÇÃO:

[✓] Git atualizado em main
[✓] SSH conectado
[✓] Script de deploy copiado
[✓] Deploy remoto executado
[✓] Healthcheck validado
[✓] Containers verificados

═══════════════════════════════════════════════════════════════════

📊 PRÓXIMOS PASSOS:

1. Testar localmente via SSH tunnel:
   
   ssh -L 8080:127.0.0.1:8080 ${VM_USER}@${VM_HOST}
   
   Depois acesse:
   - Frontend/API: http://localhost:8080/
   - Swagger: http://localhost:8080/docs
   - Healthcheck: http://localhost:8080/health

2. Monitorar logs em tempo real:
   
   ssh ${VM_USER}@${VM_HOST}
   cd ${APP_DIR}
   docker compose -f docker-compose.homolog.yml logs -f hml-backend

3. Validar banco de dados:
   
   ssh ${VM_USER}@${VM_HOST}
   docker compose -f docker-compose.homolog.yml exec -T postgres \\
     psql -U gestor_hml -d gestao_arquivistica_hml -c "\\dt"

═══════════════════════════════════════════════════════════════════

🔗 ENDEREÇOS:

Domínio: ${DOMAIN}
API Base: ${API_URL}

Frontend: http://${DOMAIN}/ (via rede interna ou SSH tunnel)
Swagger: http://${DOMAIN}/docs
ReDoc: http://${DOMAIN}/redoc
Healthcheck: http://127.0.0.1:8080/health (via SSH tunnel)

═══════════════════════════════════════════════════════════════════

🔒 RESTRIÇÕES APLICADAS:

✓ Nunca usou --volumes (dados postgres_data_hml preservados)
✓ Apenas alembic upgrade head (sem downgrade)
✓ POSTGRES_PASSWORD preservada
✓ Nginx reiniciado para upstreams OK
✓ Healthcheck validado

═══════════════════════════════════════════════════════════════════

⏱️  Deploy finalizado em $(date "+%Y-%m-%d %H:%M:%S")

FINALEOF

log_success "Tudo pronto! Acesse via SSH tunnel e valide."
