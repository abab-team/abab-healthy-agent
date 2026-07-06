param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = "",
  [string]$Port = "18001"
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_09_3_b.db"
  $db = $dbPath -replace "\\", "/"
  $DatabaseUrl = "sqlite:///$db"
}

$env:DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "backend"

Write-Host "Running Alembic migration..."
& $Python -m alembic -c backend/alembic.ini upgrade head

Write-Host "Seeding and verifying demo data..."
& $Python backend/scripts/seed_demo_data.py
& $Python backend/scripts/verify_demo_data.py

$demo = @'
from sqlalchemy import select
from app.db.session import SessionLocal
from app.modules.identity.models import User
from app.modules.family.models import Family
with SessionLocal() as session:
    gala = session.scalar(select(User).where(User.email == "gala.demo@example.com"))
    family = session.scalar(select(Family))
    print(f"{gala.id}|{family.id}")
'@ | & $Python -

$parts = $demo.Trim().Split("|")
$currentUserId = $parts[0]

Write-Host "Starting backend on port $Port..."
$out = Join-Path $env:TEMP "fha-smoke-backend.out.log"
$err = Join-Path $env:TEMP "fha-smoke-backend.err.log"
$process = Start-Process -FilePath (Resolve-Path $Python).Path `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $Port `
  -WorkingDirectory (Resolve-Path "backend").Path `
  -WindowStyle Hidden `
  -PassThru `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err

try {
  $healthStatus = $null
  for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try {
      $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 5
      $healthStatus = $response.StatusCode
      if ($healthStatus -eq 200) { break }
    } catch {
      $healthStatus = $_.Exception.Message
    }
  }
  Write-Host "HEALTH_STATUS=$healthStatus"
  if ($healthStatus -ne 200) {
    throw "health smoke failed"
  }

  $headers = @{
    "X-Current-User-Id" = $currentUserId
    "Content-Type" = "application/json"
  }
  $body = @{
    target_user_id = $currentUserId
    workflow_type = "daily_health_brief"
    user_message = "Please generate a daily health brief from system records."
    source = "mobile_backend_smoke_script"
  } | ConvertTo-Json

  $run = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs" -Method Post -Headers $headers -Body $body
  $traceId = $run.trace_id
  $tools = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/tool-calls" -Headers $headers
  $safety = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/safety-checks" -Headers $headers

  Write-Host "RUN_STATUS=$($run.status)"
  Write-Host "TRACE_ID=$traceId"
  Write-Host "TOOL_CALLS=$($tools.Count)"
  Write-Host "SAFETY_CHECKS=$($safety.Count)"
} finally {
  if ($process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force
  }
}
