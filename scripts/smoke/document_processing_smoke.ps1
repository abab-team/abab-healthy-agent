$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "sqlite+pysqlite:///$($env:TEMP -replace '\\','/')/family_health_agent_document_processing_smoke.sqlite3"
$env:AUTH_DEMO_HEADER_ENABLED = "true"

@'
from tests.api.helpers import auth_headers, client, create_user, reset_database

reset_database()
user = create_user("document_processing_smoke")
headers = auth_headers(user["id"])
upload = client.post(
    "/api/v1/documents/me/upload?document_type=checkup_report&title=Smoke%20Document",
    headers={**headers, "Content-Type": "application/pdf", "X-File-Name": "report.pdf"},
    content=b"%PDF-1.4\n",
)
assert upload.status_code == 201, upload.text
document_id = upload.json()["id"]
job = client.post(f"/api/v1/document-processing/me/documents/{document_id}/jobs", headers=headers, json={"job_type": "ocr"})
assert job.status_code == 201, job.text
job_id = job.json()["id"]
detail = client.get(f"/api/v1/document-processing/me/jobs/{job_id}", headers=headers)
assert detail.status_code == 200, detail.text
listed = client.get(f"/api/v1/document-processing/me/documents/{document_id}/jobs", headers=headers)
assert listed.status_code == 200 and len(listed.json()["items"]) == 1, listed.text
print("document_processing_smoke ok", job_id)
'@ | python -
