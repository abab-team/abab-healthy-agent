# Production Readiness Runbook

Phase 26 prepares the project for a production-style deployment review. It does
not mean the service has been launched to real users.

## Scope

This runbook covers:

- Backend deployment readiness.
- PostgreSQL and migration readiness.
- Object-storage and document security readiness.
- HTTPS, CORS, and secret-management checks.
- Production smoke commands.
- Mobile production configuration checks.

It does not cover app-store release, paid operations, formal medical compliance
certification, or real OCR / embedding / vector DB provider onboarding.

## Required Environment Posture

Before any external trial or production-like deployment:

- `ENV=production` or `APP_ENV=production`.
- `DEBUG=false`.
- `AUTH_ENABLED=true`.
- `AUTH_DEMO_HEADER_ENABLED=false`.
- `SECRET_KEY` and `JWT_SECRET_KEY` are strong random values stored outside Git.
- `DATABASE_URL` points to PostgreSQL, not SQLite or local demo credentials.
- `CORS_ORIGINS` contains explicit HTTPS origins, never `*`.
- `.env`, API keys, JWT secrets, LLM keys, OCR keys, and embedding keys are not committed.
- `OCR_STORE_RAW_TEXT=false`.
- `RAG_STORE_RAW_TEXT=false`.
- `RAG_ALLOW_EXTERNAL_KNOWLEDGE=false` unless a separate review is completed.

## Check Commands

Validate a real deployment `.env` file:

```powershell
python tools/check_production_readiness.py --env-file .env
```

Run the deterministic smoke with a temporary safe sample environment:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke/production_readiness_smoke.ps1
```

Run the same smoke against an explicit env file:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke/production_readiness_smoke.ps1 -EnvFile .env
```

## Deployment Review Checklist

- Run Alembic migrations on a copy of the target database first.
- Confirm demo seed scripts are not pointed at the production database.
- Confirm document storage persists outside the application container.
- Confirm APIs never return local file paths.
- Confirm object storage ACL, encryption, retention, and backup policies.
- Confirm logs do not include raw prompts, raw LLM responses, OCR full text, file paths, tokens, passwords, keys, SQL, or tracebacks.
- Confirm Agent workflows still use ToolExecutor, permission checks, SafetyPolicy, and trace recording.
- Confirm no frontend path sends `tool_name` or `input_data`.
- Confirm all health output says it is based on system records and does not replace doctor judgment.

## Remaining Production Risks

- Real OCR provider onboarding still needs a provider-specific privacy review.
- RAG persistent index, real embeddings, and vector DB still need schema, deletion, revocation, and permission-sync review.
- Mobile native production release still needs package signing, app-store or internal distribution setup, and physical-device QA.
- Rate limiting, advanced observability, malware scanning, and incident response are readiness items, not completed production operations.
