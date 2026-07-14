# 模块领域：开发脚本
# 领域说明：负责演示数据初始化、数据校验和本地辅助操作。
# 文件职责：业务代码文件。承载本模块的一部分领域能力或工程能力。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.modules.auth.password import hash_password  # noqa: E402
from app.modules.alerts.enums import AlertLevel, AlertSource, AlertStatus, AlertType  # noqa: E402
from app.modules.alerts.models import Alert, AlertEvent  # noqa: E402
from app.modules.document_center.enums import (  # noqa: E402
    DocumentExtractStatus,
    DocumentSource,
    DocumentType,
    DocumentVisibility,
)
from app.modules.document_center.models import DocumentVersion, MedicalDocument  # noqa: E402
from app.modules.document_processing.models import (  # noqa: E402
    DocumentExtractionResult,
    DocumentProcessingJob,
    MedicalEventDraft,
)
from app.modules.family.enums import FamilyMemberStatus, FamilyRole  # noqa: E402
from app.modules.family.models import Family, FamilyMember  # noqa: E402
from app.modules.health_data.enums import (  # noqa: E402
    BloodPressureArm,
    BloodPressureMeasurementContext,
    BloodPressurePosture,
    ConfidenceLevel,
    MetricSource,
    MetricType,
)
from app.modules.health_data.models import BloodPressureRecord, HealthMetric  # noqa: E402
from app.modules.health_profile.enums import BloodType  # noqa: E402
from app.modules.health_profile.models import HealthProfile  # noqa: E402
from app.modules.health_record.enums import (  # noqa: E402
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity.enums import Gender, UserStatus  # noqa: E402
from app.modules.identity.models import (  # noqa: E402
    LoginSession,
    RefreshToken,
    User,
    UserAuthAccount,
)
from app.modules.medical_timeline.enums import (  # noqa: E402
    MedicalEventSource,
    MedicalEventStatus,
    MedicalEventType,
)
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions.models import (  # noqa: E402
    MemberSharePermission,
    PermissionAuditLog,
)
from app.modules.reports.enums import (  # noqa: E402
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)
from app.modules.reports.models import DailyReport  # noqa: E402


DEMO_EMAILS = {
    "gala": "gala.demo@example.com",
    "father": "father.demo@example.com",
    "mother": "mother.demo@example.com",
}
DEMO_PASSWORD = "123456"
DEMO_FAMILY_NAME = "Gala 的家庭"
# Keep local QA records current so relative queries such as "recent 7 days"
# exercise the same data shown in the mobile app. A fixed date remains
# available for reproducible checks through FHA_DEMO_TODAY=YYYY-MM-DD.
DEMO_TODAY = date.fromisoformat(os.getenv("FHA_DEMO_TODAY", date.today().isoformat()))
DEMO_NOW = datetime.combine(DEMO_TODAY, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=8)


# 函数职责：业务函数，封装 开发脚本 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def clear_demo_data(session: Session) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    users = list(
        session.scalars(select(User).where(User.email.in_(DEMO_EMAILS.values()))),
    )
    user_ids = [user.id for user in users]
    families = list(
        session.scalars(select(Family).where(Family.name == DEMO_FAMILY_NAME)),
    )
    family_ids = [family.id for family in families]

    if user_ids:
        alert_ids = list(
            session.scalars(select(Alert.id).where(Alert.user_id.in_(user_ids))),
        )
        if alert_ids:
            session.execute(delete(AlertEvent).where(AlertEvent.alert_id.in_(alert_ids)))
        session.execute(delete(Alert).where(Alert.user_id.in_(user_ids)))
        session.execute(delete(DailyReport).where(DailyReport.user_id.in_(user_ids)))
        session.execute(delete(HealthRecordDraft).where(HealthRecordDraft.user_id.in_(user_ids)))
        session.execute(delete(SymptomRecord).where(SymptomRecord.user_id.in_(user_ids)))
        session.execute(delete(HealthMetric).where(HealthMetric.user_id.in_(user_ids)))
        session.execute(delete(BloodPressureRecord).where(BloodPressureRecord.user_id.in_(user_ids)))
        session.execute(delete(HealthProfile).where(HealthProfile.user_id.in_(user_ids)))
        session.execute(delete(MedicalEventDraft).where(MedicalEventDraft.user_id.in_(user_ids)))
        session.execute(delete(DocumentExtractionResult).where(DocumentExtractionResult.user_id.in_(user_ids)))
        session.execute(delete(DocumentProcessingJob).where(DocumentProcessingJob.user_id.in_(user_ids)))

        document_ids = list(
            session.scalars(select(MedicalDocument.id).where(MedicalDocument.user_id.in_(user_ids))),
        )
        if document_ids:
            session.execute(delete(DocumentVersion).where(DocumentVersion.document_id.in_(document_ids)))
        session.execute(delete(MedicalDocument).where(MedicalDocument.user_id.in_(user_ids)))
        session.execute(delete(MedicalEvent).where(MedicalEvent.user_id.in_(user_ids)))
        session.execute(delete(LoginSession).where(LoginSession.user_id.in_(user_ids)))
        session.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(user_ids)))
        session.execute(delete(UserAuthAccount).where(UserAuthAccount.user_id.in_(user_ids)))

    if family_ids:
        session.execute(delete(PermissionAuditLog).where(PermissionAuditLog.family_id.in_(family_ids)))
        session.execute(delete(MemberSharePermission).where(MemberSharePermission.family_id.in_(family_ids)))
        session.execute(delete(FamilyMember).where(FamilyMember.family_id.in_(family_ids)))
        session.execute(delete(Family).where(Family.id.in_(family_ids)))

    if user_ids:
        session.execute(delete(User).where(User.id.in_(user_ids)))
    session.flush()


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_users(session: Session) -> dict[str, User]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    users = {
        "gala": User(
            phone="demo_gala_phone",
            email=DEMO_EMAILS["gala"],
            password_hash=hash_password(DEMO_PASSWORD),
            nickname="Gala",
            gender=Gender.FEMALE,
            birth_date=date(2004, 1, 1),
            status=UserStatus.ACTIVE,
        ),
        "father": User(
            phone="demo_father_phone",
            email=DEMO_EMAILS["father"],
            password_hash=hash_password(DEMO_PASSWORD),
            nickname="爸爸",
            gender=Gender.MALE,
            birth_date=date(1974, 1, 1),
            status=UserStatus.ACTIVE,
        ),
        "mother": User(
            phone="demo_mother_phone",
            email=DEMO_EMAILS["mother"],
            password_hash=hash_password(DEMO_PASSWORD),
            nickname="妈妈",
            gender=Gender.FEMALE,
            birth_date=date(1976, 1, 1),
            status=UserStatus.ACTIVE,
        ),
    }
    session.add_all(users.values())
    session.flush()
    return users


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_family(session: Session, users: dict[str, User]) -> Family:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    family = Family(name=DEMO_FAMILY_NAME, owner_user_id=users["gala"].id)
    session.add(family)
    session.flush()
    session.add_all(
        [
            FamilyMember(
                family_id=family.id,
                user_id=users["gala"].id,
                role=FamilyRole.OWNER,
                relationship_label="本人",
                display_name="Gala",
                status=FamilyMemberStatus.ACTIVE,
                joined_at=DEMO_NOW,
            ),
            FamilyMember(
                family_id=family.id,
                user_id=users["father"].id,
                role=FamilyRole.MEMBER,
                relationship_label="爸爸",
                display_name="爸爸",
                status=FamilyMemberStatus.ACTIVE,
                joined_at=DEMO_NOW,
            ),
            FamilyMember(
                family_id=family.id,
                user_id=users["mother"].id,
                role=FamilyRole.MEMBER,
                relationship_label="妈妈",
                display_name="妈妈",
                status=FamilyMemberStatus.ACTIVE,
                joined_at=DEMO_NOW,
            ),
        ],
    )
    session.flush()
    return family


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_permissions(session: Session, family: Family, users: dict[str, User]) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    enabled = {
        "share_all": True,
        "can_view_profile": True,
        "can_view_metrics": True,
        "can_view_reports": True,
        "can_view_symptoms": True,
        "can_view_medical_events": True,
        "can_view_documents": True,
        "can_view_alerts": True,
        "can_create_alerts": True,
        "can_view_memory_summary": True,
        "can_create_symptom_records": True,
        "can_create_metric_records": True,
        "can_upload_documents": True,
        "can_create_medical_events": True,
        "can_generate_reports": True,
        "can_generate_doctor_visit_summary": True,
        "can_export_summary": True,
    }
    for user in users.values():
        session.add(MemberSharePermission(family_id=family.id, user_id=user.id, **enabled))


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_health_profiles(session: Session, users: dict[str, User]) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    profiles = [
        HealthProfile(
            user_id=users["gala"].id,
            height_cm=165,
            gender=Gender.FEMALE,
            birth_date=date(2004, 1, 1),
            blood_type=BloodType.UNKNOWN,
            health_goal="保持规律作息和基础活动量",
            chronic_conditions_summary="暂无记录",
            allergy_summary="系统内暂无记录",
            medication_summary="系统内暂无记录",
        ),
        HealthProfile(
            user_id=users["father"].id,
            height_cm=172,
            gender=Gender.MALE,
            birth_date=date(1974, 1, 1),
            blood_type=BloodType.UNKNOWN,
            health_goal="关注血压和日常活动",
            chronic_conditions_summary="系统内暂无明确慢病记录",
            allergy_summary="系统内暂无记录",
            medication_summary="系统内暂无长期用药记录",
        ),
        HealthProfile(
            user_id=users["mother"].id,
            height_cm=160,
            gender=Gender.FEMALE,
            birth_date=date(1976, 1, 1),
            blood_type=BloodType.UNKNOWN,
            health_goal="关注膝盖疼痛、活动量和睡眠",
            chronic_conditions_summary="系统内暂无明确慢病记录",
            allergy_summary="系统内暂无记录",
            medication_summary="系统内暂无长期用药记录",
        ),
    ]
    session.add_all(profiles)


# 函数职责：业务函数，封装 开发脚本 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def metric_at(days_ago: int, hour: int = 8) -> datetime:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return datetime.combine(DEMO_TODAY - timedelta(days=days_ago), datetime.min.time(), tzinfo=timezone.utc).replace(hour=hour)


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_health_metrics(session: Session, users: dict[str, User]) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    gala_series = {
        MetricType.SLEEP_DURATION: ([7.2, 6.8, 7.5, 7.0, 6.9, 7.4, 7.1], "hour"),
        MetricType.STEPS: ([8200, 7600, 9100, 6800, 7400, 8000, 8600], "steps"),
        MetricType.WEIGHT: ([56.2, 56.1, 56.3, 56.2, 56.0, 56.1, 56.2], "kg"),
        MetricType.BMI: ([20.6, 20.6, 20.7, 20.6, 20.6, 20.6, 20.6], "kg/m2"),
        MetricType.HEART_RATE: ([72, 74, 71, 73, 75, 72, 70], "bpm"),
    }
    records: list[HealthMetric] = []
    for metric_type, (values, unit) in gala_series.items():
        for days_ago, value in enumerate(values):
            records.append(
                HealthMetric(
                    user_id=users["gala"].id,
                    metric_type=metric_type,
                    value_numeric=value,
                    unit=unit,
                    measured_at=metric_at(days_ago),
                    source=MetricSource.MANUAL,
                    source_detail="phase03_demo_seed",
                    confidence_level=ConfidenceLevel.HIGH,
                    note="合成 demo 指标数据",
                ),
            )

    mother_steps = [4200, 3900, 6100, 6800, 7200, 7000, 6600]
    for days_ago, value in enumerate(mother_steps):
        records.append(
            HealthMetric(
                user_id=users["mother"].id,
                metric_type=MetricType.STEPS,
                value_numeric=value,
                unit="steps",
                measured_at=metric_at(days_ago),
                source=MetricSource.MANUAL,
                source_detail="phase03_demo_seed",
                confidence_level=ConfidenceLevel.HIGH,
                note="合成 demo 步数数据，最近两天略低用于演示",
            ),
        )

    for days_ago, value in enumerate([78, 76]):
        records.append(
            HealthMetric(
                user_id=users["father"].id,
                metric_type=MetricType.HEART_RATE,
                value_numeric=value,
                unit="bpm",
                measured_at=metric_at(days_ago, hour=20),
                source=MetricSource.MANUAL,
                source_detail="phase03_demo_seed",
                confidence_level=ConfidenceLevel.MEDIUM,
                note="合成 demo 心率数据",
            ),
        )
    session.add_all(records)


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_blood_pressure(session: Session, users: dict[str, User]) -> list[BloodPressureRecord]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    father_values = [
        (0, 145, 92, 78),
        (1, 142, 90, 80),
        (2, 146, 91, 79),
        (5, 136, 86, 76),
        (8, 132, 84, 74),
        (11, 138, 88, 82),
        (15, 130, 82, 72),
        (19, 134, 85, 75),
        (23, 128, 82, 73),
        (29, 135, 86, 77),
    ]
    gala_values = [
        (0, 118, 76, 72),
        (2, 116, 74, 70),
        (5, 119, 77, 71),
        (8, 117, 75, 69),
        (12, 120, 78, 73),
        (16, 118, 76, 71),
        (21, 121, 79, 74),
        (28, 117, 75, 70),
    ]
    record_specs = [
        (users["father"].id, *value) for value in father_values
    ] + [
        (users["gala"].id, *value) for value in gala_values
    ]
    records = [
        BloodPressureRecord(
            user_id=user_id,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            measured_at=metric_at(days_ago, hour=20 if days_ago < 3 else 7),
            measurement_context=BloodPressureMeasurementContext.EVENING if days_ago < 3 else BloodPressureMeasurementContext.MORNING,
            arm=BloodPressureArm.LEFT if days_ago % 2 == 0 else BloodPressureArm.RIGHT,
            posture=BloodPressurePosture.SITTING,
            source=MetricSource.MANUAL,
            confidence_level=ConfidenceLevel.HIGH,
            note="合成 demo 血压记录，仅用于后续规则和查询演示",
        )
        for user_id, days_ago, systolic, diastolic, pulse in record_specs
    ]
    session.add_all(records)
    session.flush()
    return records


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_symptoms(session: Session, family: Family, users: dict[str, User]) -> list[SymptomRecord]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    records = [
        SymptomRecord(
            user_id=users["mother"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            raw_text="妈妈这两天膝盖疼，走路少了。",
            symptom_name="膝盖疼",
            body_part="膝盖",
            severity=2,
            started_at=metric_at(1, hour=18),
            duration_text="近两天",
            possible_trigger="走路或活动后不适",
            related_metric_types=[MetricType.STEPS.value],
            follow_up_needed=True,
            follow_up_at=metric_at(-3, hour=9),
            status=SymptomRecordStatus.ACTIVE,
            confidence_level=ConfidenceLevel.MEDIUM,
            ai_summary="妈妈近两天有膝盖疼记录，活动量有所下降，建议继续记录变化。",
            timeline_visible=True,
            source=HealthRecordSource.MANUAL,
        ),
        SymptomRecord(
            user_id=users["mother"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            raw_text="妈妈昨晚睡得一般，今天有点疲劳。",
            symptom_name="疲劳",
            body_part=None,
            severity=1,
            started_at=metric_at(0, hour=9),
            duration_text="一天内",
            possible_trigger="睡眠不佳后感觉疲劳",
            follow_up_needed=False,
            status=SymptomRecordStatus.ACTIVE,
            confidence_level=ConfidenceLevel.MEDIUM,
            ai_summary="妈妈有一次睡眠不佳后的疲劳记录，建议继续观察作息和感受变化。",
            timeline_visible=True,
            source=HealthRecordSource.MANUAL,
        ),
        SymptomRecord(
            user_id=users["father"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            raw_text="爸爸晚上说有点头晕，测了血压偏高。",
            symptom_name="头晕",
            body_part="头部",
            severity=2,
            started_at=metric_at(0, hour=20),
            duration_text="晚间一次",
            related_metric_types=[MetricType.HEART_RATE.value],
            follow_up_needed=True,
            follow_up_at=metric_at(-1, hour=20),
            status=SymptomRecordStatus.ACTIVE,
            confidence_level=ConfidenceLevel.MEDIUM,
            ai_summary="爸爸有一次头晕记录，并关联晚间血压偏高，建议后续继续复测记录。",
            timeline_visible=True,
            source=HealthRecordSource.MANUAL,
        ),
    ]
    session.add_all(records)
    session.flush()
    session.add(
        HealthRecordDraft(
            user_id=users["father"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            target_display_name="爸爸",
            raw_text="爸爸晚上有点头晕，血压145/92，心率78。",
            draft_type=HealthRecordDraftType.MIXED_HEALTH_RECORD,
            extracted_json={
                "symptom_name": "头晕",
                "blood_pressure": "145/92",
                "heart_rate": 78,
                "target": "爸爸",
                "demo_note": "pending demo draft; not a confirmed health fact",
            },
            missing_fields=[],
            safety_flags=[],
            confidence_level=ConfidenceLevel.MEDIUM,
            status=HealthRecordDraftStatus.PENDING,
            expires_at=DEMO_NOW + timedelta(days=7),
        ),
    )
    return records


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_document(session: Session, family: Family, users: dict[str, User]) -> MedicalDocument:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    document = MedicalDocument(
        user_id=users["father"].id,
        family_id=family.id,
        uploaded_by_user_id=users["gala"].id,
        document_type=DocumentType.CHECKUP_REPORT,
        title="爸爸 Demo 体检报告",
        file_name="father_demo_checkup_report.pdf",
        file_path="demo://documents/father_demo_checkup_report.pdf",
        file_mime_type="application/pdf",
        file_size=204800,
        document_date=DEMO_TODAY - timedelta(days=14),
        hospital_or_org="Demo 体检中心",
        description="合成 demo 资料元信息，不对应真实文件。",
        ai_extract_status=DocumentExtractStatus.CONFIRMED,
        ai_summary="Demo 体检报告摘要，用于资料中心展示。",
        extracted_json={"demo": True, "source": "synthetic"},
        confirmed_at=DEMO_NOW,
        related_event_count=1,
        source=DocumentSource.UPLOAD,
        visibility=DocumentVisibility.FAMILY_SHARED,
    )
    session.add(document)
    session.flush()
    return document


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_medical_events(
    session: Session,
    family: Family,
    users: dict[str, User],
    document: MedicalDocument,
) -> list[MedicalEvent]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    events = [
        MedicalEvent(
            user_id=users["father"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            event_type=MedicalEventType.CHECKUP,
            title="2026 年家庭健康 Demo 体检记录",
            event_date=DEMO_TODAY - timedelta(days=14),
            hospital_or_org="Demo 体检中心",
            diagnosis_text=None,
            summary="Demo 体检资料记录，用于展示健康时间线。",
            doctor_advice=None,
            medications=None,
            key_findings=[
                {"type": "blood_pressure_note", "text": "血压记录需要结合日常复测观察"},
            ],
            follow_up_needed=True,
            follow_up_at=DEMO_NOW + timedelta(days=45),
            related_document_id=document.id,
            source=MedicalEventSource.MANUAL,
            confidence_level=ConfidenceLevel.MEDIUM,
            timeline_visible=True,
            status=MedicalEventStatus.ACTIVE,
        ),
        MedicalEvent(
            user_id=users["mother"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="膝盖不适观察记录",
            event_date=DEMO_TODAY - timedelta(days=1),
            hospital_or_org=None,
            diagnosis_text=None,
            summary="Demo 记录，用于后续就医摘要演示。",
            doctor_advice=None,
            medications=None,
            key_findings=[{"type": "symptom_note", "text": "近期有膝盖疼记录，可继续观察变化"}],
            follow_up_needed=True,
            follow_up_at=DEMO_NOW + timedelta(days=14),
            source=MedicalEventSource.MANUAL,
            confidence_level=ConfidenceLevel.MEDIUM,
            timeline_visible=True,
            status=MedicalEventStatus.ACTIVE,
        ),
    ]
    session.add_all(events)
    session.flush()
    return events


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_daily_reports(session: Session, family: Family, users: dict[str, User]) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    session.add_all(
        [
            DailyReport(
                user_id=users["gala"].id,
                family_id=family.id,
                report_date=DEMO_TODAY,
                overall_status="平稳",
                status_level=DailyReportStatusLevel.NORMAL,
                summary_text="今日整体状态平稳，睡眠和活动量可继续保持。",
                highlights=[{"text": "睡眠和活动量较稳定"}],
                concerns=[],
                suggestions=[{"text": "继续保持规律作息和基础活动量。"}],
                metrics_snapshot={"sleep_duration_hour": 7.2, "steps": 8200, "weight_kg": 56.2, "heart_rate_bpm": 72},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
            DailyReport(
                user_id=users["father"].id,
                family_id=family.id,
                report_date=DEMO_TODAY,
                overall_status="需要关注",
                status_level=DailyReportStatusLevel.ATTENTION,
                summary_text="近期血压记录需要关注，建议接下来几天固定时间复测并记录。如伴随明显不适，请咨询医生。",
                highlights=[],
                concerns=[{"text": "近 3 次血压记录偏高"}],
                suggestions=[{"text": "固定时间复测并继续记录。"}],
                metrics_snapshot={"recent_blood_pressure": ["145/92", "142/90", "146/91"], "pulse_range": "78-80"},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
            DailyReport(
                user_id=users["mother"].id,
                family_id=family.id,
                report_date=DEMO_TODAY,
                overall_status="需要观察",
                status_level=DailyReportStatusLevel.ATTENTION,
                summary_text="近期有膝盖疼记录，活动量略低，建议继续观察并记录变化。",
                highlights=[],
                concerns=[{"text": "近期有膝盖疼记录，最近两天步数略低"}],
                suggestions=[{"text": "继续观察疼痛和活动量变化。"}],
                metrics_snapshot={"recent_steps": [4200, 3900, 6100, 6800, 7200, 7000, 6600]},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
        ],
    )


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_alerts(
    session: Session,
    family: Family,
    users: dict[str, User],
    bp_records: list[BloodPressureRecord],
    symptoms: list[SymptomRecord],
    events: list[MedicalEvent],
) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    father_bp_alert = Alert(
        user_id=users["father"].id,
        family_id=family.id,
        created_by_user_id=None,
        alert_type=AlertType.METRIC_ATTENTION,
        level=AlertLevel.ATTENTION,
        title="近期血压记录需要关注",
        message="近几次血压记录偏高，建议固定时间复测并继续记录。如伴随明显不适，请咨询医生。",
        suggested_action="固定时间复测并记录变化。",
        related_entity_type="blood_pressure_records",
        related_entity_id=bp_records[0].id,
        trigger_reason="近 3 次血压记录偏高",
        status=AlertStatus.ACTIVE,
        source=AlertSource.RULE,
    )
    father_follow_up = Alert(
        user_id=users["father"].id,
        family_id=family.id,
        created_by_user_id=None,
        alert_type=AlertType.MEDICAL_FOLLOW_UP,
        level=AlertLevel.ATTENTION,
        title="体检后复查提醒",
        message="Demo 体检记录设置了后续关注时间，建议按计划整理资料或咨询医生。",
        suggested_action="按计划整理资料或咨询医生。",
        related_entity_type="medical_events",
        related_entity_id=events[0].id,
        trigger_reason="Demo 体检记录设置了后续关注时间",
        status=AlertStatus.ACTIVE,
        due_at=DEMO_NOW + timedelta(days=45),
        source=AlertSource.SYSTEM,
    )
    mother_symptom = Alert(
        user_id=users["mother"].id,
        family_id=family.id,
        created_by_user_id=None,
        alert_type=AlertType.SYMPTOM_FOLLOW_UP,
        level=AlertLevel.INFO,
        title="膝盖疼记录随访",
        message="妈妈近期有膝盖疼记录，建议继续观察疼痛和活动量变化。",
        suggested_action="继续记录疼痛和活动量变化。",
        related_entity_type="symptom_records",
        related_entity_id=symptoms[0].id,
        trigger_reason="近期有膝盖疼记录",
        status=AlertStatus.ACTIVE,
        source=AlertSource.RULE,
    )
    session.add_all([father_bp_alert, father_follow_up, mother_symptom])


# 函数职责：业务函数，封装 开发脚本 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def main() -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    with SessionLocal() as session:
        clear_demo_data(session)
        users = seed_users(session)
        family = seed_family(session, users)
        seed_permissions(session, family, users)
        seed_health_profiles(session, users)
        seed_health_metrics(session, users)
        bp_records = seed_blood_pressure(session, users)
        symptoms = seed_symptoms(session, family, users)
        document = seed_document(session, family, users)
        events = seed_medical_events(session, family, users, document)
        seed_daily_reports(session, family, users)
        seed_alerts(session, family, users, bp_records, symptoms, events)
        session.commit()

    print("Phase 03 demo data seeded successfully.")
    print(f"Demo users: {', '.join(DEMO_EMAILS.values())}")
    print(f"Demo family: {DEMO_FAMILY_NAME}")


if __name__ == "__main__":
    main()
