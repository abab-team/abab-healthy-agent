param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "sqlite+pysqlite:///$($env:TEMP -replace '\\','/')/family_health_agent_ocr_document_smoke.sqlite3"
$env:AUTH_DEMO_HEADER_ENABLED = "true"
$env:OCR_ENABLED = "true"
$env:OCR_PROVIDER = "mock"
$env:OCR_STORE_RAW_TEXT = "false"

@'
from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.document_processing.models import MedicalEventDraft
from app.modules.medical_timeline.models import MedicalEvent
from tests.api.helpers import auth_headers, client, create_user, reset_database

reset_database()
user = create_user("ocr_document_smoke")
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
ocr = client.post(f"/api/v1/document-processing/me/jobs/{job_id}/run-mock-ocr", headers=headers)
assert ocr.status_code == 201, ocr.text
result = ocr.json()
assert result["raw_text_excerpt"] is None
run = client.post(
    "/api/v1/agent/runs",
    headers=headers,
    json={
        "target_user_id": user["id"],
        "workflow_type": "medical_event_draft_create",
        "user_message": "Create a pending health event draft from the system OCR preview.",
        "confirmation": True,
        "workflow_payload": {
            "source_document_id": document_id,
            "extraction_result_id": result["id"],
            "draft_title": "Health document draft",
            "extracted_text_preview": "System OCR preview for a pending health event draft.",
            "structured_hints": {"suggested_event_type": "other"},
        },
    },
)
assert run.status_code == 201, run.text
assert "formal_event_created=false" in run.json()["generated_content"]
with SessionLocal() as db:
    assert len(list(db.scalars(select(MedicalEventDraft)))) == 1
    assert len(list(db.scalars(select(MedicalEvent)))) == 0
print("ocr_document_smoke ok", run.json()["trace_id"])
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
