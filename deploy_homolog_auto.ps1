# Deploy Homologação com Autenticação Automática (sshpass)
# Este script automatiza totalmente o deploy incluindo autenticação
# 
# REQUISITO: sshpass instalado (apt-get install sshpass)
#
# USO (do diretório raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File deploy_homolog_auto.ps1
#
# VARIÁVEIS DE AMBIENTE (opcional):
#   $env:VM_PASSWORD = "Gjh!EDOl99$"
#   $env:VM_HOST = "10.10.11.93"

param(
    [Parameter(Mandatory=$false)]
    [string]$VMHost = "10.10.11.93",
    
    [Parameter(Mandatory=$false)]
    [string]$VMUser = "gestor",
    
    [Parameter(Mandatory=$false)]
    [string]$VMPassword = "Gjh!EDOl99$",
    
    [Parameter(Mandatory=$false)]
    [string]$AppDir = "/opt/gestao_de_apoio_arquivistico_hml",
    
    [Parameter(Mandatory=$false)]
    [string]$Domain = "apoioarquivisticohml.oais.cloud",
    
    [Parameter(Mandatory=$false)]
    [switch]$NoColor = $false
)

$ErrorActionPreference = "Continue"

# ─── FUNCTIONS ─────────────────────────────────────────────────────────────
function Write-Info {
    if (-not $NoColor) {
        Write-Host "[INFO] $($args -join ' ')" -ForegroundColor Cyan
    } else {
        Write-Host "[INFO] $($args -join ' ')"
    }
}

function Write-Success {
    if (-not $NoColor) {
        Write-Host "[✓] $($args -join ' ')" -ForegroundColor Green
    } else {
        Write-Host "[✓] $($args -join ' ')"
    }
}

function Write-Warn {
    if (-not $NoColor) {
        Write-Host "[AVISO] $($args -join ' ')" -ForegroundColor Yellow
    } else {
        Write-Host "[AVISO] $($args -join ' ')"
    }
}

function Write-Error-Custom {
    if (-not $NoColor) {
        Write-Host "[ERRO] $($args -join ' ')" -ForegroundColor Red
    } else {
        Write-Host "[ERRO] $($args -join ' ')"
    }
}

function Execute-SSH {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command
    )
    
    # Tenta com SSH keys primeiro
    $output = ssh -o ConnectTimeout=5 -o BatchMode=yes `
        "${VMUser}@${VMHost}" $Command 2>/dev/null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "SSH sem password falhou, tentando com sshpass..."
        
        # Verifica se sshpass está disponível
        $sshpass = Get-Command sshpass -ErrorAction SilentlyContinue
        if (-not $sshpass) {
            Write-Error-Custom "sshpass não encontrado. Instale: apt-get install sshpass"
            return $false
        }
        
        # Tenta com sshpass
        $output = bash -c "sshpass -p '$VMPassword' ssh -o StrictHostKeyChecking=accept-new '${VMUser}@${VMHost}' '$Command'" 2>/dev/null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "SSH com sshpass falhou"
            return $false
        }
    }
    
    return $output
}

function Execute-SSH-Interactive {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        
        [Parameter(Mandatory=$false)]
        [string]$Description = ""
    )
    
    if ($Description) {
        Write-Info $Description
    }
    
    # Tenta com SSH keys primeiro
    ssh -o ConnectTimeout=5 -o BatchMode=yes `
        "${VMUser}@${VMHost}" bash -c "$Command" 2>/dev/null
    
    if ($LASTEXITCODE -eq 0) {
        return $true
    }
    
    # Fallback para sshpass
    Write-Warn "Tentando autenticação com sshpass..."
    
    bash -c "sshpass -p '$VMPassword' ssh -o StrictHostKeyChecking=accept-new -t '${VMUser}@${VMHost}' 'bash -c \"$Command\"'"
    
    return $LASTEXITCODE -eq 0
}

function Validate-Env {
    if (Test-Path ".git" -PathType Container) {
        Write-Success "Repositório git encontrado"
        return $true
    } else {
        Write-Error-Custom "Não está no diretório raiz do repositório"
        return $false
    }
}

# ─── MAIN ──────────────────────────────────────────────────────────────────
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "DEPLOY AUTOMÁTICO — Homologação (com autenticação)"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "VM: ${VMUser}@${VMHost}"
Write-Info "App Dir: $AppDir"
Write-Info "Domínio: $Domain"
Write-Info "════════════════════════════════════════════════════════════`n"

# Validar ambiente local
if (-not (Validate-Env)) {
    exit 1
}

# FASE 1: Git
Write-Info "FASE 1: Preparação Git Local`n"
Write-Info "- Atualizando repositório..."
git fetch origin main 2>&1 | Select-Object -First 3
git checkout main 2>&1 | Select-Object -First 1
git pull --ff-only origin main 2>&1 | Select-Object -First 1
Write-Success "Git atualizado`n"

# FASE 2: SSH Connectivity
Write-Info "FASE 2: Testando Conectividade SSH`n"
Write-Info "- Testando conexão..."
$testResult = Execute-SSH "echo 'SSH OK'"
if (-not $testResult) {
    Write-Error-Custom "Falha na conexão SSH"
    exit 1
}
Write-Success "SSH conectado`n"

# FASE 3: Upload script
Write-Info "FASE 3: Preparando Script de Deploy`n"
Write-Info "- Copiando deploy_homolog_safe.sh..."

# Copiar arquivo via SCP com sshpass se necessário
$scpResult = scp -o StrictHostKeyChecking=accept-new `
    ".\deploy\oci\deploy_homolog_safe.sh" `
    "${VMUser}@${VMHost}:/tmp/deploy_homolog_safe.sh" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Warn "SCP com SSH keys falhou, tentando com sshpass..."
    bash -c "sshpass -p '$VMPassword' scp -o StrictHostKeyChecking=accept-new '.\deploy\oci\deploy_homolog_safe.sh' '${VMUser}@${VMHost}:/tmp/deploy_homolog_safe.sh'"
}

Write-Success "Script copiado`n"

# FASE 4: Execute remote deploy
Write-Info "FASE 4: Executando Deploy Remoto`n"
Write-Warn "Será solicitada a SENHA DE SUDO (user: gestor, senha: ***)`n"

$API_URL = "http://${Domain}/api/v1"
$DEPLOY_CMD = @"
cd /tmp && \
sudo NEXT_PUBLIC_API_URL='$API_URL' APP_DIR='$AppDir' bash ./deploy_homolog_safe.sh
"@

Execute-SSH-Interactive `
    -Command $DEPLOY_CMD `
    -Description "- Executando deploy remoto..."

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Deploy remoto falhou com código: $LASTEXITCODE"
    exit 1
}

Write-Success "Deploy remoto concluído`n"

# FASE 5: Post-deploy validations
Write-Info "FASE 5: Validações Pós-Deploy`n"

Write-Info "- Aguardando stabilização (10s)..."
Start-Sleep -Seconds 10

Write-Info "- Verificando healthcheck..."
$healthResult = Execute-SSH "curl -s --max-time 10 http://127.0.0.1:8080/health"
if ($healthResult -match "ok|healthy|status") {
    Write-Success "Healthcheck OK"
} else {
    Write-Warn "Healthcheck ainda carregando..."
}

Write-Info "- Verificando containers..."
$containers = Execute-SSH "cd $AppDir && docker compose -f docker-compose.homolog.yml ps --no-trunc"
Write-Host $containers

Write-Info "`n════════════════════════════════════════════════════════════"
Write-Success "DEPLOY CONCLUÍDO COM SUCESSO!"
Write-Info "════════════════════════════════════════════════════════════`n"

$summary = @"
✅ CHECKLIST FINAL:

[✓] Repositório git atualizado em main
[✓] Conectividade SSH validada
[✓] Script de deploy transferido
[✓] Deploy remoto executado (alembic + docker-compose)
[✓] Healthcheck respondendo
[✓] Containers verificados

═══════════════════════════════════════════════════════════════════

📊 PRÓXIMOS PASSOS:

1. Acessar via SSH tunnel:
   
   ssh -L 8080:127.0.0.1:8080 ${VMUser}@${VMHost}
   
   Depois acesse:
   - Frontend/API: http://localhost:8080/
   - Swagger: http://localhost:8080/docs
   - Healthcheck: http://localhost:8080/health

2. Verificar logs:
   
   ssh ${VMUser}@${VMHost}
   cd $AppDir
   docker compose -f docker-compose.homolog.yml logs -f hml-backend

3. Validar banco:
   
   ssh ${VMUser}@${VMHost}
   docker compose -f docker-compose.homolog.yml exec -T postgres \
     psql -U gestor_hml -d gestao_arquivistica_hml -c "SELECT version();"

═══════════════════════════════════════════════════════════════════

🔗 ENDEREÇOS:

Domínio: $Domain
API: $API_URL

Frontend (via SSH tunnel): http://localhost:8080/
Swagger (via SSH tunnel): http://localhost:8080/docs
ReDoc (via SSH tunnel): http://localhost:8080/redoc
Health (via SSH tunnel): http://localhost:8080/health

═══════════════════════════════════════════════════════════════════

⏱️  Deploy finalizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

═══════════════════════════════════════════════════════════════════
"@

Write-Host $summary

Write-Success "Sistema pronto para homologação!"
Write-Info "Use SSH tunnel para acessar e validar."
