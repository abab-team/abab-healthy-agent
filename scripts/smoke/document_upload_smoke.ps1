param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "sqlite+pysqlite:///$($env:TEMP -replace '\\','/')/family_health_agent_document_upload_smoke.sqlite3"
$env:AUTH_DEMO_HEADER_ENABLED = "true"

@'
from tests.api.helpers import auth_headers, client, create_user, reset_database

reset_database()
user = create_user("document_upload_smoke")
headers = {**auth_headers(user["id"]), "Content-Type": "application/pdf", "X-File-Name": "../report.pdf"}
response = client.post(
    "/api/v1/documents/me/upload?document_type=checkup_report&title=Smoke%20Document",
    headers=headers,
    content=b"%PDF-1.4\n",
)
assert response.status_code == 201, response.text
body = response.json()
assert "file_path" not in body
assert body["file_name"] == "report.pdf"
print("document_upload_smoke ok", body["id"])
'@ | & $Python -
