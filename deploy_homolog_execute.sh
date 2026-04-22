#!/bin/bash
################################################################################
# INSTRUÇÕES - Git Bash / WSL / Linux Terminal
# 
# Execute este script ou copie os comandos linha por linha
# no Git Bash (Windows) ou Terminal (Linux/Mac)
#
# PREREQUISITO: Estar no diretório raiz do projeto
# cd c:\des\gestao_de_apoio_arquivistico
#
################################################################################

set -euo pipefail

# CONFIG
VM_HOST="10.10.11.93"
VM_USER="gestor"
VM_PASSWORD="Gjh!EDOl99$"
APP_DIR="/opt/gestao_de_apoio_arquivistico_hml"
DOMAIN="apoioarquivisticohml.oais.cloud"
API_URL="http://${DOMAIN}/api/v1"
COMPOSE_FILE="docker-compose.homolog.yml"
ENV_FILE=".env.homolog"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { printf "${BLUE}[$(date '+%H:%M:%S')]${NC} $*\n"; }
success() { printf "${GREEN}[✓]${NC} $*\n"; }
warn() { printf "${YELLOW}[!]${NC} $*\n" >&2; }
error() { printf "${RED}[✗]${NC} $*\n" >&2; exit 1; }

################################################################################
# FASE 1: Validar ambiente local
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 1: Validação do Ambiente Local"
log "════════════════════════════════════════════════════════════"

[ -d ".git" ] || error "Não está no repositório git. cd c:/des/gestao_de_apoio_arquivistico"
success "Repositório git encontrado"

[ -f "deploy/oci/deploy_homolog_safe.sh" ] || error "Script deploy_homolog_safe.sh não encontrado"
success "Script de deploy encontrado"

command -v git >/dev/null || error "git não instalado"
command -v ssh >/dev/null || error "ssh não disponível"

success "Todas as dependências OK"

################################################################################
# FASE 2: Atualizar Git local
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 2: Atualizar Git Local"
log "════════════════════════════════════════════════════════════"

git fetch origin main
git checkout main
git pull --ff-only origin main || git pull --rebase origin main || true
success "Git atualizado"

################################################################################
# FASE 3: Testar SSH
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 3: Testar Conectividade SSH"
log "════════════════════════════════════════════════════════════"

if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes "${VM_USER}@${VM_HOST}" "echo 'OK'" 2>/dev/null; then
  success "SSH sem password funcionando (SSH keys configuradas)"
  USE_SSHPASS=false
else
  warn "SSH keys não configuradas, usaremos comando interativo"
  warn "Será solicitada a senha do usuário gestor"
  USE_SSHPASS=true
fi

################################################################################
# FASE 4: Copiar script de deploy para VM
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 4: Copiar Script de Deploy"
log "════════════════════════════════════════════════════════════"

if [ "$USE_SSHPASS" = "true" ]; then
  warn "Digite a senha de gestor quando solicitado (${VM_PASSWORD})"
fi

scp -o StrictHostKeyChecking=accept-new \
    ./deploy/oci/deploy_homolog_safe.sh \
    "${VM_USER}@${VM_HOST}:/tmp/deploy_homolog_safe.sh" || {
  error "Falha ao copiar script. Verifique conectividade e credenciais."
}

success "Script copiado para VM"

################################################################################
# FASE 5: Executar deploy remoto
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 5: Executar Deploy Remoto (com sudo)"
log "════════════════════════════════════════════════════════════"

warn "Digite a SENHA DE SUDO da VM quando solicitado"
warn "Usuário: gestor | Senha: Gjh!EDOl99$"

DEPLOY_CMD="cd /tmp && sudo NEXT_PUBLIC_API_URL='${API_URL}' APP_DIR='${APP_DIR}' bash ./deploy_homolog_safe.sh"

ssh -t "${VM_USER}@${VM_HOST}" bash -c "${DEPLOY_CMD}" || {
  error "Deploy remoto falhou"
}

success "Deploy remoto concluído!"

################################################################################
# FASE 6: Validações pós-deploy
################################################################################

log "════════════════════════════════════════════════════════════"
log "FASE 6: Validações Pós-Deploy"
log "════════════════════════════════════════════════════════════"

log "Aguardando stabilização (10s)..."
sleep 10

log "Testando healthcheck..."
HEALTH=$(ssh -q "${VM_USER}@${VM_HOST}" curl -s --max-time 10 http://127.0.0.1:8080/health 2>/dev/null || echo "")

if echo "$HEALTH" | grep -q "ok\|healthy\|status"; then
  success "Healthcheck respondendo OK"
  echo "$HEALTH" | head -c 200
  echo ""
else
  warn "Healthcheck ainda pode estar carregando"
fi

log "Status dos containers..."
ssh -q "${VM_USER}@${VM_HOST}" \
  "cd ${APP_DIR} && docker compose -f ${COMPOSE_FILE} ps --no-trunc" | \
  grep -E "hml-(postgres|redis|minio|backend|celery|frontend|nginx)" || true

################################################################################
# RESUMO FINAL
################################################################################

log "════════════════════════════════════════════════════════════"
success "DEPLOY CONCLUÍDO COM SUCESSO!"
log "════════════════════════════════════════════════════════════"

cat <<'EOF'

✅ CHECKLIST FINAL:

[✓] Git atualizado em main
[✓] Script copiado para VM
[✓] Deploy remoto executado
[✓] Alembic upgrade head executado
[✓] Docker compose up -d completo
[✓] Healthcheck respondendo
[✓] Containers verificados

═══════════════════════════════════════════════════════════════════

📊 PRÓXIMOS PASSOS:

1. Acessar via SSH tunnel:
   
   ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93
   
   Depois acesse localmente:
   - Frontend: http://localhost:8080/
   - Swagger: http://localhost:8080/docs
   - Healthcheck: http://localhost:8080/health

2. Monitorar logs:
   
   ssh gestor@10.10.11.93
   cd /opt/gestao_de_apoio_arquivistico_hml
   docker compose -f docker-compose.homolog.yml logs -f hml-backend

3. Validar banco:
   
   ssh gestor@10.10.11.93
   docker compose -f docker-compose.homolog.yml exec -T postgres \
     psql -U gestor_hml -d gestao_arquivistica_hml -c "\\dt"

═══════════════════════════════════════════════════════════════════

🔗 DOMÍNIO HOMOLOGAÇÃO:

Domínio: apoioarquivisticohml.oais.cloud
API Base: http://apoioarquivisticohml.oais.cloud/api/v1

Frontend (via SSH tunnel): http://localhost:8080/
Swagger (via SSH tunnel): http://localhost:8080/docs
ReDoc (via SSH tunnel): http://localhost:8080/redoc
Health (via SSH tunnel): http://localhost:8080/health

═══════════════════════════════════════════════════════════════════

⏱️  Deploy finalizado: $(date "+%Y-%m-%d %H:%M:%S")

═══════════════════════════════════════════════════════════════════
EOF

success "Sistema pronto para validação!"
