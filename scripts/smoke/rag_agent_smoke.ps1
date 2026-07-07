param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_14_rag_agent.db"
  $db = $dbPath -replace "\\", "/"
  $DatabaseUrl = "sqlite:///$db"
}

$env:DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "backend"
$env:RAG_ENABLED = "true"
$env:AUTH_DEMO_HEADER_ENABLED = "true"

Write-Host "Running Alembic migration..."
& $Python -m alembic -c backend/alembic.ini upgrade head

Write-Host "Seeding and verifying demo data..."
& $Python backend/scripts/seed_demo_data.py
& $Python backend/scripts/verify_demo_data.py

$script = @'
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.modules.identity.models import User

get_settings.cache_clear()
client = TestClient(app)
with SessionLocal() as session:
    user = session.scalar(select(User).where(User.email == "gala.demo@example.com"))
    user_id = str(user.id)

headers = {"X-Current-User-Id": user_id}
run = client.post(
    "/api/v1/agent/runs",
    headers=headers,
    json={
        "target_user_id": user_id,
        "workflow_type": "daily_health_brief",
        "user_message": "Generate daily health brief from system records.",
        "source": "rag_agent_smoke",
    },
)
print(f"RUN_STATUS={run.status_code}")
body = run.json()
print(f"AGENT_STATUS={body.get('status')}")
trace_id = body.get("trace_id")
tools = client.get(f"/api/v1/agent/runs/{trace_id}/tool-calls", headers=headers)
safety = client.get(f"/api/v1/agent/runs/{trace_id}/safety-checks", headers=headers)
print(f"TOOL_CALL_STATUS={tools.status_code}")
print(f"SAFETY_STATUS={safety.status_code}")
print(f"SAFETY_CHECKS={len(safety.json()) if safety.status_code == 200 else 0}")
text = (run.text + tools.text + safety.text).lower()
for forbidden in ("file_path", "raw_extracted_text", "token", "password", "api_key", "traceback", "select "):
    if forbidden in text:
        raise SystemExit(f"unsafe marker leaked: {forbidden}")
if run.status_code != 201 or body.get("status") != "completed":
    raise SystemExit(run.text)
if tools.status_code != 200 or safety.status_code != 200:
    raise SystemExit("agent trace queries failed")
'@

$script | & $Python -
