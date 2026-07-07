param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Python)) {
  $resolvedPython = Get-Command python -ErrorAction SilentlyContinue
  if ($resolvedPython) {
    $Python = $resolvedPython.Source
  }
}

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_12_mobile_auth.db"
  $db = $dbPath -replace "\\", "/"
  $DatabaseUrl = "sqlite:///$db"
}

$env:DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "backend"
$env:JWT_SECRET_KEY = "mobile-auth-smoke-local-secret"
$env:AUTH_DEMO_HEADER_ENABLED = "false"

Write-Host "Running Alembic migration..."
& $Python -m alembic -c backend/alembic.ini upgrade head

Write-Host "Seeding and verifying demo data..."
& $Python backend/scripts/seed_demo_data.py
& $Python backend/scripts/verify_demo_data.py

@'
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
login = client.post("/api/v1/auth/login", json={"email": "gala.demo@example.com", "password": "DemoPass123!"})
print(f"LOGIN_STATUS={login.status_code}")
if login.status_code != 200:
    raise SystemExit(login.text)
body = login.json()
access_token = body["access_token"]
user_id = body["user"]["id"]
headers = {"Authorization": f"Bearer {access_token}"}
brief_payload = {
    "target_user_id": user_id,
    "workflow_type": "daily_health_brief",
    "user_message": "Please create a daily health brief based on system records.",
    "source": "mobile_auth_smoke",
}
run = client.post(
    "/api/v1/agent/runs",
    headers=headers,
    json=brief_payload,
)
print(f"RUN_STATUS={run.status_code}")
if run.status_code != 201:
    raise SystemExit(run.text)
trace_id = run.json()["trace_id"]
trace = client.get(f"/api/v1/agent/runs/{trace_id}", headers=headers)
tool_calls = client.get(f"/api/v1/agent/runs/{trace_id}/tool-calls", headers=headers)
safety_checks = client.get(f"/api/v1/agent/runs/{trace_id}/safety-checks", headers=headers)
print(f"TRACE_STATUS={trace.status_code}")
print(f"TOOL_CALLS_STATUS={tool_calls.status_code}")
print(f"SAFETY_CHECKS_STATUS={safety_checks.status_code}")
if trace.status_code != 200 or tool_calls.status_code != 200 or safety_checks.status_code != 200:
    raise SystemExit("auth mode agent query failed")
demo_denied = client.post(
    "/api/v1/agent/runs",
    headers={"X-Current-User-Id": user_id},
    json=brief_payload,
)
print(f"DEMO_HEADER_DISABLED_RUN_STATUS={demo_denied.status_code}")
if demo_denied.status_code != 401:
    raise SystemExit(demo_denied.text)
print("STATUS=OK")
'@ | & $Python -
