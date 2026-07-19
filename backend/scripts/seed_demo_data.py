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
LEGACY_DEMO_EMAILS = {"son.demo@example.com"}
DEMO_PASSWORD = "123456"
DEMO_FAMILY_NAME = "Gala 的家庭"
LEGACY_DEMO_FAMILY_NAMES = {"儿子的家庭"}
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
        session.scalars(select(User).where(User.email.in_([*DEMO_EMAILS.values(), *LEGACY_DEMO_EMAILS]))),
    )
    user_ids = [user.id for user in users]
    families = list(
        session.scalars(select(Family).where(Family.name.in_([DEMO_FAMILY_NAME, *LEGACY_DEMO_FAMILY_NAMES]))),
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
            gender=Gender.MALE,
            birth_date=date(2006, 1, 1),
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
            birth_date=date(1976, 7, 15),
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
            height_cm=182,
            gender=Gender.MALE,
            birth_date=date(2006, 1, 1),
            blood_type=BloodType.A,
            health_goal="保持规律睡眠和偶尔运动的记录习惯",
            chronic_conditions_summary="系统内暂无相关记录",
            allergy_summary="系统内暂无相关记录",
            medication_summary="系统内暂无相关记录",
        ),
        HealthProfile(
            user_id=users["father"].id,
            height_cm=175,
            gender=Gender.MALE,
            birth_date=date(1974, 1, 1),
            blood_type=BloodType.UNKNOWN,
            health_goal="记录血压、睡眠和日常活动",
            chronic_conditions_summary="系统内暂无相关记录",
            allergy_summary="系统内暂无相关记录",
            medication_summary="系统内暂无相关记录",
        ),
        HealthProfile(
            user_id=users["mother"].id,
            height_cm=160,
            gender=Gender.FEMALE,
            birth_date=date(1976, 7, 15),
            blood_type=BloodType.UNKNOWN,
            health_goal="保持运动习惯并记录睡眠和体重",
            chronic_conditions_summary="系统内暂无相关记录",
            allergy_summary="系统内暂无相关记录",
            medication_summary="系统内暂无相关记录",
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


def recorded_at(year: int, month: int, day: int, hour: int = 8) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_health_metrics(session: Session, users: dict[str, User]) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    records: list[HealthMetric] = []

    def add_metric(
        member: str,
        metric_type: MetricType,
        value: float,
        unit: str,
        measured_at: datetime,
        note: str | None = None,
    ) -> None:
        records.append(
            HealthMetric(
                user_id=users[member].id,
                metric_type=metric_type,
                value_numeric=value,
                unit=unit,
                measured_at=measured_at,
                source=MetricSource.MANUAL,
                source_detail="family_health_demo_v1",
                confidence_level=ConfidenceLevel.HIGH,
                note=note,
            ),
        )

    for day, value, quality in [(20, 7.2, "良好"), (28, 6.5, "一般")]:
        add_metric("gala", MetricType.SLEEP_DURATION, value, "hours", recorded_at(2026, 6, day), f"睡眠质量：{quality}")
    add_metric("gala", MetricType.SLEEP_DURATION, 6.8, "hours", recorded_at(2026, 7, 8), "睡眠质量：良好")
    for month, day, value in [(6, 20, 72), (7, 5, 68), (7, 12, 70)]:
        add_metric("gala", MetricType.HEART_RATE, value, "bpm", recorded_at(2026, month, day))
    add_metric("gala", MetricType.EXERCISE_DURATION, 40, "minutes", recorded_at(2026, 6, 22), "步行")
    add_metric("gala", MetricType.EXERCISE_DURATION, 30, "minutes", recorded_at(2026, 7, 2), "跑步")
    for day, value in [(4, 6520), (7, 7120), (10, 6800)]:
        add_metric("gala", MetricType.STEPS, value, "steps", recorded_at(2026, 7, day))
    add_metric("gala", MetricType.WEIGHT, 65, "kg", recorded_at(2026, 7, 10))
    add_metric("gala", MetricType.BMI, 19.6, "kg/m2", recorded_at(2026, 7, 10))

    for month, day, value in [(6, 18, 76), (7, 10, 74)]:
        add_metric("father", MetricType.HEART_RATE, value, "bpm", recorded_at(2026, month, day))
    add_metric("father", MetricType.SLEEP_DURATION, 6.2, "hours", recorded_at(2026, 6, 20))
    add_metric("father", MetricType.SLEEP_DURATION, 6.5, "hours", recorded_at(2026, 7, 5))
    add_metric("father", MetricType.EXERCISE_DURATION, 30, "minutes", recorded_at(2026, 6, 22), "快走")
    add_metric("father", MetricType.EXERCISE_DURATION, 40, "minutes", recorded_at(2026, 7, 8), "散步")
    add_metric("father", MetricType.WEIGHT, 78, "kg", recorded_at(2026, 7, 10))
    add_metric("father", MetricType.BMI, 25.5, "kg/m2", recorded_at(2026, 7, 10))

    add_metric("mother", MetricType.BLOOD_GLUCOSE, 5.4, "mmol/L", recorded_at(2026, 6, 10), "空腹血糖")
    for month, day, value in [(6, 18, 6.0), (7, 3, 5.8), (7, 12, 6.3)]:
        add_metric("mother", MetricType.SLEEP_DURATION, value, "hours", recorded_at(2026, month, day))
    add_metric("mother", MetricType.EXERCISE_DURATION, 30, "minutes", recorded_at(2026, 6, 25), "瑜伽")
    add_metric("mother", MetricType.EXERCISE_DURATION, 45, "minutes", recorded_at(2026, 7, 9), "散步")
    add_metric("mother", MetricType.WEIGHT, 62, "kg", recorded_at(2026, 7, 8))
    add_metric("mother", MetricType.BMI, 24.2, "kg/m2", recorded_at(2026, 7, 8))
    session.add_all(records)


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_blood_pressure(session: Session, users: dict[str, User]) -> list[BloodPressureRecord]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    record_specs = [
        ("gala", 2026, 6, 18, 126, 82),
        ("gala", 2026, 6, 26, 121, 78),
        ("gala", 2026, 7, 10, 118, 76),
        ("father", 2026, 4, 15, 148, 94),
        ("father", 2026, 5, 20, 142, 90),
        ("father", 2026, 6, 18, 145, 92),
        ("father", 2026, 7, 10, 138, 88),
        ("mother", 2026, 5, 20, 126, 82),
        ("mother", 2026, 6, 15, 124, 80),
        ("mother", 2026, 7, 8, 128, 83),
    ]
    records = [
        BloodPressureRecord(
            user_id=users[member].id,
            systolic=systolic,
            diastolic=diastolic,
            pulse=None,
            measured_at=recorded_at(year, month, day),
            measurement_context=BloodPressureMeasurementContext.UNKNOWN,
            arm=BloodPressureArm.UNKNOWN,
            posture=BloodPressurePosture.SITTING,
            source=MetricSource.MANUAL,
            confidence_level=ConfidenceLevel.HIGH,
            note="家庭健康 Demo 数据集 V1：用户提供的血压记录。",
        )
        for member, year, month, day, systolic, diastolic in record_specs
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
            user_id=users["father"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            raw_text="偶尔头晕，约持续 10 分钟。",
            symptom_name="头晕",
            body_part="头部",
            severity=None,
            started_at=recorded_at(2026, 6, 25),
            duration_text="约 10 分钟",
            possible_trigger=None,
            related_metric_types=None,
            follow_up_needed=False,
            status=SymptomRecordStatus.ACTIVE,
            confidence_level=ConfidenceLevel.HIGH,
            ai_summary="已记录：偶尔头晕，约持续 10 分钟。",
            timeline_visible=True,
            source=HealthRecordSource.MANUAL,
        ),
        SymptomRecord(
            user_id=users["mother"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            raw_text="颈肩酸痛，持续 2 天，已自行缓解。",
            symptom_name="颈肩酸痛",
            body_part="颈肩部",
            severity=None,
            started_at=recorded_at(2026, 7, 1),
            duration_text="2 天",
            possible_trigger=None,
            follow_up_needed=False,
            status=SymptomRecordStatus.RESOLVED,
            confidence_level=ConfidenceLevel.HIGH,
            ai_summary="已记录：颈肩酸痛持续 2 天，备注为已自行缓解。",
            timeline_visible=True,
            source=HealthRecordSource.MANUAL,
        ),
    ]
    session.add_all(records)
    session.flush()
    return records


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_documents(session: Session, family: Family, users: dict[str, User]) -> dict[str, MedicalDocument]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    documents = {
        "father_checkup": MedicalDocument(
            user_id=users["father"].id,
            family_id=family.id,
            uploaded_by_user_id=users["gala"].id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="体检报告（2026 年）",
            file_name="father_checkup_2026.pdf",
            file_path="demo://documents/father_checkup_2026.pdf",
            file_mime_type="application/pdf",
            document_date=date(2026, 5, 10),
            description="家庭健康 Demo 数据集 V1：体检报告资料条目。",
            ai_extract_status=DocumentExtractStatus.CONFIRMED,
            related_event_count=1,
            source=DocumentSource.UPLOAD,
            visibility=DocumentVisibility.FAMILY_SHARED,
        ),
        "father_bp": MedicalDocument(
            user_id=users["father"].id,
            family_id=family.id,
            uploaded_by_user_id=users["gala"].id,
            document_type=DocumentType.MEDICAL_RECORD,
            title="血压测量记录",
            file_name="father_blood_pressure_records.pdf",
            file_path="demo://documents/father_blood_pressure_records.pdf",
            file_mime_type="application/pdf",
            document_date=date(2026, 7, 10),
            description="家庭健康 Demo 数据集 V1：血压测量资料条目。",
            ai_extract_status=DocumentExtractStatus.CONFIRMED,
            source=DocumentSource.UPLOAD,
            visibility=DocumentVisibility.FAMILY_SHARED,
        ),
        "mother_checkup": MedicalDocument(
            user_id=users["mother"].id,
            family_id=family.id,
            uploaded_by_user_id=users["gala"].id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="年度体检报告",
            file_name="mother_annual_checkup.pdf",
            file_path="demo://documents/mother_annual_checkup.pdf",
            file_mime_type="application/pdf",
            document_date=date(2026, 3, 15),
            description="家庭健康 Demo 数据集 V1：年度体检资料条目。",
            ai_extract_status=DocumentExtractStatus.CONFIRMED,
            related_event_count=1,
            source=DocumentSource.UPLOAD,
            visibility=DocumentVisibility.FAMILY_SHARED,
        ),
        "mother_glucose": MedicalDocument(
            user_id=users["mother"].id,
            family_id=family.id,
            uploaded_by_user_id=users["gala"].id,
            document_type=DocumentType.LAB_TEST,
            title="血糖检测记录",
            file_name="mother_glucose_record.pdf",
            file_path="demo://documents/mother_glucose_record.pdf",
            file_mime_type="application/pdf",
            document_date=date(2026, 6, 10),
            description="家庭健康 Demo 数据集 V1：空腹血糖 5.4 mmol/L 的资料条目。",
            ai_extract_status=DocumentExtractStatus.CONFIRMED,
            source=DocumentSource.UPLOAD,
            visibility=DocumentVisibility.FAMILY_SHARED,
        ),
    }
    session.add_all(documents.values())
    session.flush()
    return documents


# 函数职责：演示数据流程，写入固定演示数据，保证本地开发和验收结果可复现。
# 业务边界：演示数据脚本应尽量幂等，重复执行不应制造脏数据。
def seed_medical_events(
    session: Session,
    family: Family,
    users: dict[str, User],
    documents: dict[str, MedicalDocument],
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
            event_type=MedicalEventType.FOLLOW_UP,
            title="血压相关复诊记录",
            event_date=date(2026, 5, 10),
            hospital_or_org=None,
            diagnosis_text=None,
            summary="已完成的复查记录。",
            doctor_advice=None,
            medications=None,
            key_findings=[
                {"type": "record_type", "text": "血压相关复诊记录"},
            ],
            follow_up_needed=True,
            follow_up_at=recorded_at(2026, 8, 10),
            related_document_id=documents["father_checkup"].id,
            source=MedicalEventSource.MANUAL,
            confidence_level=ConfidenceLevel.MEDIUM,
            timeline_visible=True,
            status=MedicalEventStatus.ACTIVE,
        ),
        MedicalEvent(
            user_id=users["mother"].id,
            family_id=family.id,
            created_by_user_id=users["gala"].id,
            event_type=MedicalEventType.CHECKUP,
            title="年度体检",
            event_date=date(2026, 3, 15),
            hospital_or_org=None,
            diagnosis_text=None,
            summary="已完成的年度体检记录。",
            doctor_advice=None,
            medications=None,
            key_findings=[{"type": "record_type", "text": "年度体检"}],
            follow_up_needed=False,
            related_document_id=documents["mother_checkup"].id,
            source=MedicalEventSource.MANUAL,
            confidence_level=ConfidenceLevel.MEDIUM,
            timeline_visible=True,
            status=MedicalEventStatus.ARCHIVED,
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
                overall_status="记录摘要",
                status_level=DailyReportStatusLevel.NORMAL,
                summary_text="系统内有血压、心率、睡眠、运动和体重记录。",
                highlights=[{"text": "最近一次血压记录为 118/76 mmHg"}],
                concerns=[],
                suggestions=[{"text": "可继续保持规律睡眠和运动记录。"}],
                metrics_snapshot={"latest_blood_pressure": "118/76", "weight_kg": 65, "bmi": 19.6},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
            DailyReport(
                user_id=users["father"].id,
                family_id=family.id,
                report_date=DEMO_TODAY,
                overall_status="记录摘要",
                status_level=DailyReportStatusLevel.ATTENTION,
                summary_text="系统内有血压、心率、睡眠、运动、症状、复诊和资料记录。",
                highlights=[{"text": "最近一次血压记录为 138/88 mmHg"}],
                concerns=[],
                suggestions=[{"text": "已设置每周测量血压和 2026-08-10 复查提醒。"}],
                metrics_snapshot={"recent_blood_pressure": ["148/94", "142/90", "145/92", "138/88"], "weight_kg": 78, "bmi": 25.5},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
            DailyReport(
                user_id=users["mother"].id,
                family_id=family.id,
                report_date=DEMO_TODAY,
                overall_status="记录摘要",
                status_level=DailyReportStatusLevel.ATTENTION,
                summary_text="系统内有血压、空腹血糖、睡眠、运动、症状、年度体检和资料记录。",
                highlights=[{"text": "最近一次血压记录为 128/83 mmHg"}],
                concerns=[],
                suggestions=[{"text": "已设置年度体检和保持运动习惯提醒。"}],
                metrics_snapshot={"latest_blood_pressure": "128/83", "fasting_blood_glucose_mmol_l": 5.4, "weight_kg": 62, "bmi": 24.2},
                generated_by=DailyReportGeneratedBy.SYSTEM,
                generation_status=DailyReportGenerationStatus.SUCCESS,
            ),
        ],
    )


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
        seed_blood_pressure(session, users)
        seed_symptoms(session, family, users)
        documents = seed_documents(session, family, users)
        seed_medical_events(session, family, users, documents)
        seed_daily_reports(session, family, users)
        session.commit()

    print("Phase 03 demo data seeded successfully.")
    print(f"Demo users: {', '.join(DEMO_EMAILS.values())}")
    print(f"Demo family: {DEMO_FAMILY_NAME}")


if __name__ == "__main__":
    main()
