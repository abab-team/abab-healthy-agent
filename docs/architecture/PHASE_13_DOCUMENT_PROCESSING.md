# Phase 13 Document Processing Flow

Phase 13 closes the minimal document-processing loop:

1. Upload a PDF/PNG/JPG/JPEG document into controlled local storage.
2. Create and query a `document_processing_job`.
3. Run deterministic mock OCR when `OCR_ENABLED=true`.
4. Store only a safe OCR preview/extraction summary by default.
5. Generate a pending `medical_event_draft` through the existing Agent workflow.

## Safety Boundaries

- OCR output is not a diagnosis.
- OCR output is not a prescription.
- OCR output is not a medication dosage suggestion.
- OCR output is not a formal health fact.
- Draft generation does not create formal `medical_events`.
- API responses do not return local absolute paths, `file_path`, raw OCR full text, API keys, tracebacks, or SQL.
- `medical_event_draft_create` remains a confirmed Agent workflow and does not expose generic tool execution.

## Configuration

```env
DOCUMENT_UPLOAD_ENABLED=true
DOCUMENT_MAX_UPLOAD_MB=10
DOCUMENT_STORAGE_BACKEND=local
DOCUMENT_STORAGE_DIR=backend/storage/documents
DOCUMENT_ALLOWED_MIME_TYPES=application/pdf,image/png,image/jpeg

OCR_ENABLED=false
OCR_PROVIDER=mock
OCR_TIMEOUT_SECONDS=30
OCR_MAX_TEXT_CHARS=8000
OCR_STORE_RAW_TEXT=false
```

`OCR_ENABLED=false` is the default. Mock OCR must be explicitly enabled in local smoke or test environments.

## Upload Contract

The Phase 13 upload endpoint accepts a raw request body with:

- `Content-Type`: `application/pdf`, `image/png`, or `image/jpeg`
- `X-File-Name`: display filename to sanitize
- query fields such as `document_type`, `title`, and `visibility`

The database stores an internal storage key such as `documents/<uuid>.pdf`, not a machine-local absolute path.

## Current Limits

- No real OCR provider is integrated.
- No OCR queue worker is integrated.
- No mobile native file picker is implemented in this phase.
- No formal document-to-medical-event confirmation flow is implemented.
- No diagnosis, prescription, dosage, or stop-medication advice is generated.
