param(
  [string]$Python = ".\.venv-smoke\Scripts\python.exe",
  [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_14_rag.db"
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

response = client.post(
    "/api/v1/rag/search",
    headers={"X-Current-User-Id": user_id},
    json={
        "query": "blood pressure symptoms reminders",
        "target_user_id": user_id,
        "top_k": 5,
    },
)
print(f"RAG_STATUS={response.status_code}")
body = response.json()
print(f"RAG_ENABLED={body.get('rag_enabled')}")
print(f"RAG_RESULT_COUNT={body.get('result_count')}")
text = response.text.lower()
for forbidden in ("file_path", "raw_extracted_text", "token", "password", "api_key", "traceback"):
    if forbidden in text:
        raise SystemExit(f"unsafe marker leaked: {forbidden}")
if response.status_code != 200:
    raise SystemExit(response.text)
'@

$script | & $Python -
