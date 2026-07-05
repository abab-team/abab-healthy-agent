# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：策略文件。集中维护权限或安全策略，避免调用方各自实现造成规则不一致。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations


SAFE_DENIED_MESSAGE = "你目前没有权限查看该成员的这类健康数据。可以请对方在家庭共享设置中开启相关权限。"

VIEW_PERMISSION_FIELDS = {
    "profile": "can_view_profile",
    "metrics": "can_view_metrics",
    "reports": "can_view_reports",
    "symptoms": "can_view_symptoms",
    "medical_events": "can_view_medical_events",
    "documents": "can_view_documents",
    "alerts": "can_view_alerts",
    "memory_summary": "can_view_memory_summary",
}

CREATE_PERMISSION_FIELDS = {
    "symptoms": "can_create_symptom_records",
    "metrics": "can_create_metric_records",
    "documents": "can_upload_documents",
    "medical_events": "can_create_medical_events",
    "alerts": "can_create_alerts",
}

GENERATE_PERMISSION_FIELDS = {
    "reports": "can_generate_reports",
    "doctor_visit_summary": "can_generate_doctor_visit_summary",
}

SHARE_ALL_VIEW_TYPES = {
    "profile",
    "metrics",
    "reports",
    "symptoms",
    "medical_events",
    "alerts",
    "memory_summary",
}


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def permission_field_for(permission_type: str, action: str) -> str | None:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    if action == "view":
        return VIEW_PERMISSION_FIELDS.get(permission_type)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if action in {"create", "update", "delete"}:
        return CREATE_PERMISSION_FIELDS.get(permission_type)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if action == "generate":
        return GENERATE_PERMISSION_FIELDS.get(permission_type)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if action == "export":
        return "can_export_summary"
    return None


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def denied_reason_for(permission_type: str, action: str) -> str:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    if permission_type == "documents":
        return "documents_not_shared"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if permission_type == "symptoms":
        return "symptoms_not_shared"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if permission_type == "medical_events":
        return "medical_events_not_shared"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if action in {"create", "update", "delete"}:
        return "create_not_allowed"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if action == "export":
        return "export_not_allowed"
    return "permission_denied"
