from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase05_api.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("JWT_SECRET_KEY", "api-test-jwt-secret")
os.environ.setdefault("AUTH_DEMO_HEADER_ENABLED", "true")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.alerts.models import Alert, AlertEvent  # noqa: E402
from app.modules.document_center.models import DocumentVersion, MedicalDocument  # noqa: E402
from app.modules.document_processing.models import DocumentExtractionResult, DocumentProcessingJob, MedicalEventDraft  # noqa: E402
from app.modules.family.models import Family, FamilyInvitation, FamilyMember  # noqa: E402
from app.modules.health_data.models import BloodPressureRecord, HealthMetric  # noqa: E402
from app.modules.health_profile.models import HealthProfile  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.identity.enums import Gender  # noqa: E402
from app.modules.identity.models import LoginSession, RefreshToken, User, UserAuthAccount  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permission_service  # noqa: E402
from app.modules.permissions.models import MemberSharePermission, PermissionAuditLog  # noqa: E402


client = TestClient(app)


def reset_database() -> None:
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.execute(delete(AlertEvent))
        db.execute(delete(Alert))
        db.execute(delete(DocumentExtractionResult))
        db.execute(delete(MedicalEventDraft))
        db.execute(delete(DocumentProcessingJob))
        db.execute(delete(DocumentVersion))
        db.execute(delete(MedicalEvent))
        db.execute(delete(MedicalDocument))
        db.execute(delete(HealthRecordDraft))
        db.execute(delete(SymptomRecord))
        db.execute(delete(BloodPressureRecord))
        db.execute(delete(HealthMetric))
        db.execute(delete(HealthProfile))
        db.execute(delete(PermissionAuditLog))
        db.execute(delete(MemberSharePermission))
        db.execute(delete(FamilyInvitation))
        db.execute(delete(FamilyMember))
        db.execute(delete(Family))
        db.execute(delete(LoginSession))
        db.execute(delete(RefreshToken))
        db.execute(delete(UserAuthAccount))
        db.execute(delete(User))
        db.commit()
    engine.dispose()


def create_user(prefix: str, *, nickname: str | None = None) -> dict[str, Any]:
    payload = {
        "email": f"{prefix}.{uuid.uuid4().hex}@example.com",
        "phone": f"{prefix}_{uuid.uuid4().hex[:16]}",
        "nickname": nickname or prefix,
        "gender": Gender.UNKNOWN.value,
    }
    response = client.post("/api/v1/identity/users", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(user_id: str) -> dict[str, str]:
    return {"X-Current-User-Id": user_id}


def create_family(owner_id: str, *, name: str = "API Test Family") -> dict[str, Any]:
    response = client.post(
        "/api/v1/families",
        headers=auth_headers(owner_id),
        json={"name": f"{name} {uuid.uuid4().hex[:8]}", "owner_display_name": "本人"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_member(family_id: str, actor_id: str, user_id: str, label: str, display_name: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/families/{family_id}/members",
        headers=auth_headers(actor_id),
        json={
            "user_id": user_id,
            "relationship_label": label,
            "display_name": display_name,
            "role": "member",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_permission_for_member(family_id: str, user_id: str, *, share_all: bool = True) -> None:
    with SessionLocal() as db:
        permission_service.create_default_permissions_for_member(
            db,
            family_id=uuid.UUID(family_id),
            user_id=uuid.UUID(user_id),
        )
        permission_service.update_share_permission(
            db,
            actor_user_id=uuid.UUID(user_id),
            family_id=uuid.UUID(family_id),
            target_user_id=uuid.UUID(user_id),
            updates={"share_all": share_all},
            reason="api_test_fixture",
        )
        db.commit()


def count_permission_audit_logs() -> int:
    with SessionLocal() as db:
        return len(list(db.scalars(select(PermissionAuditLog.id))))
