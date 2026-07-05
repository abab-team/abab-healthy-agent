# 模块领域：开发脚本
# 领域说明：负责演示数据初始化、数据校验和本地辅助操作。
# 文件职责：业务代码文件。承载本模块的一部分领域能力或工程能力。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND_DIR = Path(__file__).resolve().parents[1]
# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
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


# 函数职责：业务函数，封装 开发脚本 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def count_for_user_ids(model: type, user_ids: list) -> int:
    # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model).where(model.user_id.in_(user_ids))) or 0


# 函数职责：业务函数，封装 开发脚本 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def main() -> None:
    # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
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
            "permissions_with_alert_create": session.scalar(
                select(func.count())
                .select_from(MemberSharePermission)
                .where(
                    MemberSharePermission.family_id == family_id,
                    MemberSharePermission.can_create_alerts.is_(True),
                ),
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
        "permissions_with_alert_create": 3,
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
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for name, value in checks.items():
        print(f"- {name}: {value}")

    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if failures:
        print("Verification failed:")
        # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
        for failure in failures:
            print(f"- {failure}")
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise SystemExit(1)

    print("Verification passed.")


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    main()
