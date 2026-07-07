# Document Processing QA Checklist

Phase 13 adds a minimal mobile UI for the document-processing loop. It is not a production upload experience.

## Mock Mode

- Open the mobile app in mock mode.
- Visit the Health Documents page.
- Confirm the list shows mock documents only.
- Open a document detail page.
- Confirm the page states that upload, OCR, and draft generation are mock/static.
- Confirm no raw OCR text, file path, API key, traceback, SQL, diagnosis, prescription, dosage, or stop-medication wording is displayed.

## API Mode Web

- Start the backend locally.
- Confirm `/health` returns 200.
- Use `document_upload_smoke.ps1` to create a safe uploaded document.
- Open the mobile app in API mode.
- Visit the Health Documents page.
- Confirm API documents can be listed.
- Open a document detail page.
- Create a processing job.
- If `OCR_ENABLED=true`, run mock OCR and confirm only a safe preview is shown.
- Generate a health event draft through the controlled Agent workflow, not through generic tool execution.

## Expo Go Device

- Phone and computer must be on the same Wi-Fi.
- Do not use `localhost` from the phone.
- Use the computer LAN IP for the API base URL.
- If LAN access fails, try Expo tunnel for the frontend and verify backend reachability separately.

## Safety Checks

- OCR preview must not be described as a diagnosis.
- OCR preview must not create a formal health fact.
- Draft generation must create only a pending draft after confirmation.
- The UI must not show `raw_extracted_text`, `file_path`, raw long text, token, password, API key, traceback, SQL, or local machine paths.
- If mock OCR is disabled, the UI must show a clear error or pending state, not a fake success.
