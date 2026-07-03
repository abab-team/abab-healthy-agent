from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.modules.alerts.models import Alert  # noqa: E402
from app.modules.document_center.models import MedicalDocument  # noqa: E402
from app.modules.family.models import Family, FamilyMember  # noqa: E402
from app.modules.health_data.models import BloodPressureRecord, HealthMetric  # noqa: E402
from app.modules.health_profile.models import HealthProfile  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity.models import User  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions.models import MemberSharePermission  # noqa: E402
from app.modules.reports.models import DailyReport  # noqa: E402


DEMO_EMAILS = {
    "gala.demo@example.com",
    "father.demo@example.com",
    "mother.demo@example.com",
}
DEMO_FAMILY_NAME = "Gala 的家庭"


def count_for_user_ids(model: type, user_ids: list) -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model).where(model.user_id.in_(user_ids))) or 0


def main() -> None:
    with SessionLocal() as session:
        users = list(session.scalars(select(User).where(User.email.in_(DEMO_EMAILS))))
        user_ids = [user.id for user in users]
        family = session.scalar(select(Family).where(Family.name == DEMO_FAMILY_NAME))
        family_id = family.id if family else None

        checks = {
            "demo_users": len(users),
            "demo_family": 1 if family else 0,
            "family_members": session.scalar(
                select(func.count()).select_from(FamilyMember).where(FamilyMember.family_id == family_id),
            )
            if family_id
            else 0,
            "permissions": session.scalar(
                select(func.count()).select_from(MemberSharePermission).where(MemberSharePermission.family_id == family_id),
            )
            if family_id
            else 0,
            "health_profiles": session.scalar(
                select(func.count()).select_from(HealthProfile).where(HealthProfile.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "health_metrics": session.scalar(
                select(func.count()).select_from(HealthMetric).where(HealthMetric.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "father_blood_pressure_records": session.scalar(
                select(func.count())
                .select_from(BloodPressureRecord)
                .join(User, BloodPressureRecord.user_id == User.id)
                .where(User.email == "father.demo@example.com"),
            ),
            "mother_symptom_records": session.scalar(
                select(func.count())
                .select_from(SymptomRecord)
                .join(User, SymptomRecord.user_id == User.id)
                .where(User.email == "mother.demo@example.com"),
            ),
            "health_record_drafts": session.scalar(
                select(func.count()).select_from(HealthRecordDraft).where(HealthRecordDraft.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "medical_events": session.scalar(
                select(func.count()).select_from(MedicalEvent).where(MedicalEvent.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "medical_documents": session.scalar(
                select(func.count()).select_from(MedicalDocument).where(MedicalDocument.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "daily_reports": session.scalar(
                select(func.count()).select_from(DailyReport).where(DailyReport.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
            "alerts": session.scalar(
                select(func.count()).select_from(Alert).where(Alert.user_id.in_(user_ids)),
            )
            if user_ids
            else 0,
        }

    expectations = {
        "demo_users": 3,
        "demo_family": 1,
        "family_members": 3,
        "permissions": 3,
        "health_profiles": 3,
        "father_blood_pressure_records": 10,
        "mother_symptom_records": 2,
        "daily_reports": 3,
        "alerts": 3,
    }
    failures = [
        f"{name}: expected >= {minimum}, got {checks.get(name, 0)}"
        for name, minimum in expectations.items()
        if checks.get(name, 0) < minimum
    ]

    print("Phase 03 demo data verification summary:")
    for name, value in checks.items():
        print(f"- {name}: {value}")

    if failures:
        print("Verification failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Verification passed.")


if __name__ == "__main__":
    main()
