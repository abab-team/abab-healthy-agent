param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = "",
  [string]$Port = "18016"
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_16_chat.db"
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
with SessionLocal() as session:
    gala = session.scalar(select(User).where(User.email == "gala.demo@example.com"))
    print(str(gala.id))
'@ | & $Python -

$currentUserId = $demo.Trim()

Write-Host "Starting backend on port $Port..."
$out = Join-Path $env:TEMP "fha-chat-smoke-backend.out.log"
$err = Join-Path $env:TEMP "fha-chat-smoke-backend.err.log"
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
    workflow_type = "chat"
    user_message = "How are my blood pressure records in the last 7 days?"
    source = "phase_16_chat_smoke"
  } | ConvertTo-Json

  $run = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs" -Method Post -Headers $headers -Body $body
  $traceId = $run.trace_id
  $tools = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/tool-calls" -Headers $headers
  $safety = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/safety-checks" -Headers $headers

  Write-Host "RUN_STATUS=$($run.status)"
  Write-Host "WORKFLOW_TYPE=$($run.workflow_type)"
  Write-Host "TRACE_ID=$traceId"
  Write-Host "TOOL_CALLS=$($tools.Count)"
  Write-Host "SAFETY_CHECKS=$($safety.Count)"

  if ($run.workflow_type -ne "chat" -or $run.status -ne "completed") {
    throw "chat workflow smoke failed"
  }
  if ($tools.Count -lt 1) {
    throw "chat workflow did not call the controlled readonly tool"
  }
  if (($run.generated_content -match "file_path|raw_extracted_text|token|password|api_key")) {
    throw "chat workflow leaked unsafe content"
  }
} finally {
  if ($process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force
  }
}
