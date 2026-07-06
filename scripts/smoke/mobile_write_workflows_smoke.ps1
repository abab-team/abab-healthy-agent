param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = "",
  [string]$Port = "18003"
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_09_3_d.db"
  $db = $dbPath -replace "\\", "/"
  $DatabaseUrl = "sqlite:///$db"
}

$env:DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "backend"

Write-Host "This smoke script uses demo DB data and creates test drafts/alerts."
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
$familyId = $parts[1]

function Get-RecordCounts {
  $script = @'
from sqlalchemy import func, select
from app.db.session import SessionLocal
from app.modules.alerts.models import Alert
from app.modules.document_processing.models import MedicalEventDraft
from app.modules.health_record.models import HealthRecordDraft
with SessionLocal() as session:
    health_drafts = session.scalar(select(func.count()).select_from(HealthRecordDraft))
    event_drafts = session.scalar(select(func.count()).select_from(MedicalEventDraft))
    alerts = session.scalar(select(func.count()).select_from(Alert))
    print(f"{health_drafts}|{event_drafts}|{alerts}")
'@
  $raw = $script | & $Python -
  $items = $raw.Trim().Split("|")
  return @{
    HealthDrafts = [int]$items[0]
    EventDrafts = [int]$items[1]
    Alerts = [int]$items[2]
  }
}

function Assert-Equal {
  param(
    [string]$Name,
    [int]$Expected,
    [int]$Actual
  )
  if ($Expected -ne $Actual) {
    throw "$Name expected $Expected but got $Actual"
  }
}

function Assert-Increment {
  param(
    [string]$Name,
    [int]$Before,
    [int]$After
  )
  if ($After -ne ($Before + 1)) {
    throw "$Name expected increment from $Before to $($Before + 1), got $After"
  }
}

Write-Host "Starting backend on port $Port..."
$out = Join-Path $env:TEMP "fha-write-smoke-backend.out.log"
$err = Join-Path $env:TEMP "fha-write-smoke-backend.err.log"
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

  function Invoke-AgentRun {
    param(
      [string]$WorkflowType,
      [bool]$Confirmation,
      [hashtable]$Payload,
      [string]$Message
    )
    $body = @{
      target_user_id = $currentUserId
      family_id = $familyId
      workflow_type = $WorkflowType
      user_message = $Message
      confirmation = $Confirmation
      source = "mobile_write_workflows_smoke_script"
      workflow_payload = $Payload
    } | ConvertTo-Json -Depth 8

    $run = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs" -Method Post -Headers $headers -Body $body
    $traceId = $run.trace_id
    $tools = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/tool-calls" -Headers $headers
    $safety = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/agent/runs/$traceId/safety-checks" -Headers $headers
    Write-Host "$WorkflowType confirmation=$Confirmation status=$($run.status) trace=$traceId tools=$($tools.Count) safety=$($safety.Count)"
    return $run
  }

  $counts = Get-RecordCounts

  $symptomPayload = @{
    raw_text = "Mild head discomfort after work; record keeping only."
    target_display_name = "Gala"
  }
  Invoke-AgentRun -WorkflowType "symptom_draft_create" -Confirmation $false -Payload $symptomPayload -Message "Create a symptom draft preview from user note."
  $afterPreview = Get-RecordCounts
  Assert-Equal -Name "symptom preview health draft count" -Expected $counts.HealthDrafts -Actual $afterPreview.HealthDrafts
  Invoke-AgentRun -WorkflowType "symptom_draft_create" -Confirmation $true -Payload $symptomPayload -Message "Create a confirmed symptom draft from user note."
  $afterConfirm = Get-RecordCounts
  Assert-Increment -Name "symptom confirm health draft count" -Before $counts.HealthDrafts -After $afterConfirm.HealthDrafts

  $counts = $afterConfirm
  $eventPayload = @{
    title = "Follow-up note"
    summary = "Routine follow-up information for demo smoke."
    draft_event_type = "follow_up"
    event_date = "2026-07-06"
  }
  Invoke-AgentRun -WorkflowType "medical_event_draft_create" -Confirmation $false -Payload $eventPayload -Message "Create a health event draft preview from user note."
  $afterPreview = Get-RecordCounts
  Assert-Equal -Name "event preview draft count" -Expected $counts.EventDrafts -Actual $afterPreview.EventDrafts
  Invoke-AgentRun -WorkflowType "medical_event_draft_create" -Confirmation $true -Payload $eventPayload -Message "Create a confirmed health event draft from user note."
  $afterConfirm = Get-RecordCounts
  Assert-Increment -Name "event confirm draft count" -Before $counts.EventDrafts -After $afterConfirm.EventDrafts

  $counts = $afterConfirm
  $alertPayload = @{
    title = "Demo health reminder"
    message = "Remember to record a routine health note."
    alert_type = "medical_follow_up"
    level = "info"
    due_at = "2026-07-07T09:00:00+08:00"
  }
  Invoke-AgentRun -WorkflowType "alert_create" -Confirmation $false -Payload $alertPayload -Message "Create a health reminder preview."
  $afterPreview = Get-RecordCounts
  Assert-Equal -Name "alert preview count" -Expected $counts.Alerts -Actual $afterPreview.Alerts
  Invoke-AgentRun -WorkflowType "alert_create" -Confirmation $true -Payload $alertPayload -Message "Create a confirmed health reminder."
  $afterConfirm = Get-RecordCounts
  Assert-Increment -Name "alert confirm count" -Before $counts.Alerts -After $afterConfirm.Alerts

  Write-Host "WRITE_WORKFLOWS_SMOKE=passed"
} finally {
  if ($process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force
  }
}
