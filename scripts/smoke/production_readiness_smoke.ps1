param(
    [string]$Python = "python",
    [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "== Phase 26 production readiness smoke =="
Write-Host "Using Python: $Python"

$tempFile = $null
try {
    if ([string]::IsNullOrWhiteSpace($EnvFile)) {
        $tempFile = Join-Path $env:TEMP "family-health-agent-production-readiness.env"
        @"
ENV=production
APP_ENV=production
DEBUG=false
AUTH_ENABLED=true
AUTH_DEMO_HEADER_ENABLED=false
SECRET_KEY=prod-secret-example-1234567890abcdef
JWT_SECRET_KEY=prod-jwt-secret-example-1234567890abcdef
DATABASE_URL=postgresql+psycopg://prod_user:prod_password@db.example.internal:5432/family_health
CORS_ORIGINS=https://app.example.com,https://admin.example.com
OCR_STORE_RAW_TEXT=false
RAG_STORE_RAW_TEXT=false
RAG_ALLOW_EXTERNAL_KNOWLEDGE=false
LLM_ENABLED=false
LLM_PROVIDER=mock
"@ | Set-Content -LiteralPath $tempFile -Encoding UTF8
        $EnvFile = $tempFile
    }

    & $Python tools/check_production_readiness.py --env-file $EnvFile
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "production_readiness_smoke ok"
}
finally {
    if ($tempFile -and (Test-Path -LiteralPath $tempFile)) {
        Remove-Item -LiteralPath $tempFile -Force
    }
}
