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
  $dbPath = Join-Path (Resolve-Path "backend\storage").Path "smoke_phase_12_auth.db"
  $db = $dbPath -replace "\\", "/"
  $DatabaseUrl = "sqlite:///$db"
}

$env:DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "backend"
$env:JWT_SECRET_KEY = "auth-smoke-local-secret"

Write-Host "Running Alembic migration..."
& $Python -m alembic -c backend/alembic.ini upgrade head

Write-Host "Seeding demo data..."
& $Python backend/scripts/seed_demo_data.py

@'
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
login = client.post(
    "/api/v1/auth/login",
    json={"email": "gala.demo@example.com", "password": "DemoPass123!"},
)
print(f"LOGIN_STATUS={login.status_code}")
if login.status_code != 200:
    raise SystemExit(login.text)
body = login.json()
access_token = body["access_token"]
refresh_token = body["refresh_token"]
me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
print(f"ME_STATUS={me.status_code}")
if me.status_code != 200:
    raise SystemExit(me.text)
refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
print(f"REFRESH_STATUS={refresh.status_code}")
if refresh.status_code != 200:
    raise SystemExit(refresh.text)
rotated_refresh = refresh.json()["refresh_token"]
old_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
print(f"OLD_REFRESH_STATUS={old_refresh.status_code}")
if old_refresh.status_code != 401:
    raise SystemExit(old_refresh.text)
logout = client.post("/api/v1/auth/logout", json={"refresh_token": rotated_refresh})
print(f"LOGOUT_STATUS={logout.status_code}")
if logout.status_code != 200:
    raise SystemExit(logout.text)
after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": rotated_refresh})
print(f"AFTER_LOGOUT_REFRESH_STATUS={after_logout.status_code}")
if after_logout.status_code != 401:
    raise SystemExit(after_logout.text)
print("STATUS=OK")
'@ | & $Python -
