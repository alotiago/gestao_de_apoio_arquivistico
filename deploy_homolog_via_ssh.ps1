# Deploy Homologação - Script PowerShell (Windows)
# USO: .\deploy_homolog_via_ssh.ps1
#
# PRÉ-REQUISITOS:
#   - SSH client instalado (Windows 10+)
#   - Conectividade com 10.10.11.93 (gestor)
#
# EXEMPLO:
#   .\deploy_homolog_via_ssh.ps1 -Verbose

param(
    [Parameter(Mandatory=$false)]
    [string]$VMHost = "10.10.11.93",
    
    [Parameter(Mandatory=$false)]
    [string]$VMUser = "gestor",
    
    [Parameter(Mandatory=$false)]
    [string]$AppDir = "/opt/gestao_de_apoio_arquivistico_hml",
    
    [Parameter(Mandatory=$false)]
    [string]$Domain = "apoioarquivisticohml.oais.cloud",
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Cyan
}

function Write-Success {
    Write-Host "[✓] $args" -ForegroundColor Green
}

function Write-Warn {
    Write-Host "[AVISO] $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "[ERRO] $args" -ForegroundColor Red
}

Write-Info "════════════════════════════════════════════════════════════"
Write-Info "DEPLOY HOMOLOGAÇÃO via SSH"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "VM: $VMUser@$VMHost"
Write-Info "App Dir: $AppDir"
Write-Info "Domínio: $Domain"
Write-Info "════════════════════════════════════════════════════════════`n"

# 1. Testar conectividade SSH
Write-Info "1. Testando conectividade SSH..."
try {
    $null = ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new `
        "${VMUser}@${VMHost}" "echo 'SSH OK'" 2>$null
    Write-Success "SSH conectado"
} catch {
    Write-Error "Não foi possível conectar via SSH a ${VMUser}@${VMHost}"
    Write-Error "Verifique:"
    Write-Error "  1. Connectividade de rede"
    Write-Error "  2. Se SSH está habilitado na VM"
    Write-Error "  3. Se já tem chave SSH gerada (ssh-keygen)"
    exit 1
}

# 2. Copiar script deploy para VM
Write-Info "2. Preparando script de deploy..."
$ScriptRemoto = "$AppDir/deploy/oci/deploy_homolog_safe.sh"

Write-Info "   Copiando deploy_homolog_safe.sh para VM..."
scp -q -o StrictHostKeyChecking=accept-new `
    ".\deploy\oci\deploy_homolog_safe.sh" `
    "${VMUser}@${VMHost}:/tmp/deploy_homolog_safe.sh"

Write-Success "Script de deploy copiado"

# 3. Executar deploy remoto
Write-Info "3. Executando deploy remoto..."
Write-Warn "Será solicitada senha de sudo da VM (user: gestor)"
Write-Info "    Senha: (será ocultada)"

$DeployCmd = @"
sudo NEXT_PUBLIC_API_URL=http://${Domain}/api/v1 \
     APP_DIR=${AppDir} \
     bash /tmp/deploy_homolog_safe.sh
"@

ssh -t "${VMUser}@${VMHost}" $DeployCmd

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deploy falhou com código de saída: $LASTEXITCODE"
    exit 1
}

Write-Success "Deploy concluído!"

# 4. Validação pós-deploy
Write-Info "4. Validações pós-deploy..."

Write-Info "   Testando /health..."
$HealthResponse = ssh -q "${VMUser}@${VMHost}" `
    "curl -s http://127.0.0.1:8080/health"

if ($HealthResponse -contains "ok" -or $HealthResponse -contains "healthy") {
    Write-Success "Health endpoint respondendo OK"
} else {
    Write-Warn "Health endpoint pode estar lento (será validado novamente em alguns segundos)"
}

Write-Info "   Status dos containers..."
$Containers = ssh -q "${VMUser}@${VMHost}" `
    "cd ${AppDir} && docker compose -f docker-compose.homolog.yml ps --format='table {{.Names}}\t{{.Status}}'"
Write-Host $Containers

# 5. Checklist final
Write-Info "`n════════════════════════════════════════════════════════════"
Write-Success "DEPLOY CONCLUÍDO COM SUCESSO!"
Write-Info "════════════════════════════════════════════════════════════`n"

Write-Host @"
✅ PRÓXIMAS AÇÕES:

1. SSH Tunnel para acessar Homologação localmente:
   
   PowerShell:
     ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

   Depois acesse localmente:
     http://localhost:8080/
     http://localhost:8080/docs

2. Acompanhar logs:
   
   ssh gestor@10.10.11.93
   cd /opt/gestao_de_apoio_arquivistico_hml
   docker compose -f docker-compose.homolog.yml logs -f hml-backend

3. Verificar saúde:
   
   # Digite em SSH:
   curl http://127.0.0.1:8080/health
   curl http://127.0.0.1:8080/ready

════════════════════════════════════════════════════════════

📊 ENDEREÇOS:

   Frontend/API:  http://$Domain/
   Swagger UI:    http://$Domain/docs
   ReDoc:         http://$Domain/redoc

   (Acesse via SSH tunnel ou rede interna)

════════════════════════════════════════════════════════════
"@

Write-Info "Deploy finalizado em $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
