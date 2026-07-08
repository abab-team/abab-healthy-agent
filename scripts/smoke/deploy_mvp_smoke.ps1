param(
    [string]$Python = "python",
    [int]$BackendPort = 18015
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "== Phase 15 MVP deployment smoke =="
Write-Host "Using Python: $Python"

& $Python -m compileall backend/app backend/tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/mobile_backend_smoke.ps1 -Python $Python -Port $BackendPort
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/auth_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/document_upload_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/document_processing_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/ocr_document_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/rag_retrieval_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File scripts/smoke/rag_agent_smoke.ps1 -Python $Python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "deploy_mvp_smoke ok"
