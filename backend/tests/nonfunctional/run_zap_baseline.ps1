param(
    [string]$TargetUrl = $(if ($env:ZAP_TARGET_URL) { $env:ZAP_TARGET_URL } else { "http://localhost:8000" }),
    [int]$MaxMinutes = 5
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$reportsDir = Join-Path $scriptDir "reports"
New-Item -Path $reportsDir -ItemType Directory -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$htmlReport = "zap-baseline-$timestamp.html"
$jsonReport = "zap-baseline-$timestamp.json"
$markdownReport = "zap-baseline-$timestamp.md"

Write-Host "Executando OWASP ZAP baseline"
Write-Host "Alvo: $TargetUrl"
Write-Host "Relatórios: $reportsDir"

$dockerArgs = @(
    "run", "--rm", "-t",
    "-v", "${reportsDir}:/zap/wrk:rw",
    "ghcr.io/zaproxy/zaproxy:stable",
    "zap-baseline.py",
    "-t", $TargetUrl,
    "-m", $MaxMinutes,
    "-r", $htmlReport,
    "-J", $jsonReport,
    "-w", $markdownReport
)

& docker @dockerArgs

if ($LASTEXITCODE -eq 2) {
    Write-Warning "OWASP ZAP baseline concluiu com alertas de warning. Relatórios foram gerados para análise."
}
elseif ($LASTEXITCODE -ne 0) {
    Write-Error "OWASP ZAP baseline finalizou com erro (exit code $LASTEXITCODE)"
    exit $LASTEXITCODE
}

Write-Host "Execução concluída com sucesso"
Write-Host "HTML: $(Join-Path $reportsDir $htmlReport)"
Write-Host "JSON: $(Join-Path $reportsDir $jsonReport)"
Write-Host "Markdown: $(Join-Path $reportsDir $markdownReport)"