# 模块领域：审计模块
# 领域说明：负责记录敏感数据访问、隐私相关操作和 Agent 执行痕迹。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：AuditAction 约束 审计模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AuditAction(StrEnum):
    # 枚举说明：CREATE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    CREATE = "create"
    # 枚举说明：UPDATE 是该枚举允许出现的一个业务取值。
    UPDATE = "update"
    # 枚举说明：DELETE 是该枚举允许出现的一个业务取值。
    DELETE = "delete"
    # 枚举说明：VIEW 是该枚举允许出现的一个业务取值。
    VIEW = "view"
    # 枚举说明：EXPORT 是该枚举允许出现的一个业务取值。
    EXPORT = "export"
    # 枚举说明：SHARE 是该枚举允许出现的一个业务取值。
    SHARE = "share"
    # 枚举说明：LOGIN 是该枚举允许出现的一个业务取值。
    LOGIN = "login"
    # 枚举说明：LOGOUT 是该枚举允许出现的一个业务取值。
    LOGOUT = "logout"
    # 枚举说明：PERMISSION_CHANGE 是该枚举允许出现的一个业务取值。
    PERMISSION_CHANGE = "permission_change"
    # 枚举说明：AGENT_RUN 是该枚举允许出现的一个业务取值。
    AGENT_RUN = "agent_run"
    # 枚举说明：TOOL_CALL 是该枚举允许出现的一个业务取值。
    TOOL_CALL = "tool_call"
    # 枚举说明：SAFETY_BLOCK 是该枚举允许出现的一个业务取值。
    SAFETY_BLOCK = "safety_block"


# 类职责：AuditResourceType 约束 审计模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AuditResourceType(StrEnum):
    # 枚举说明：USER 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    USER = "user"
    # 枚举说明：FAMILY 是该枚举允许出现的一个业务取值。
    FAMILY = "family"
    # 枚举说明：FAMILY_MEMBER 是该枚举允许出现的一个业务取值。
    FAMILY_MEMBER = "family_member"
    # 枚举说明：PERMISSION 是该枚举允许出现的一个业务取值。
    PERMISSION = "permission"
    # 枚举说明：HEALTH_PROFILE 是该枚举允许出现的一个业务取值。
    HEALTH_PROFILE = "health_profile"
    # 枚举说明：HEALTH_METRIC 是该枚举允许出现的一个业务取值。
    HEALTH_METRIC = "health_metric"
    # 枚举说明：BLOOD_PRESSURE_RECORD 是该枚举允许出现的一个业务取值。
    BLOOD_PRESSURE_RECORD = "blood_pressure_record"
    # 枚举说明：SYMPTOM_RECORD 是该枚举允许出现的一个业务取值。
    SYMPTOM_RECORD = "symptom_record"
    # 枚举说明：MEDICAL_EVENT 是该枚举允许出现的一个业务取值。
    MEDICAL_EVENT = "medical_event"
    # 枚举说明：MEDICAL_DOCUMENT 是该枚举允许出现的一个业务取值。
    MEDICAL_DOCUMENT = "medical_document"
    # 枚举说明：DAILY_REPORT 是该枚举允许出现的一个业务取值。
    DAILY_REPORT = "daily_report"
    # 枚举说明：ALERT 是该枚举允许出现的一个业务取值。
    ALERT = "alert"
    # 枚举说明：AGENT_TRACE 是该枚举允许出现的一个业务取值。
    AGENT_TRACE = "agent_trace"
    # 枚举说明：EXPORT_FILE 是该枚举允许出现的一个业务取值。
    EXPORT_FILE = "export_file"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"


# 类职责：DataAccessCategory 约束 审计模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DataAccessCategory(StrEnum):
    # 枚举说明：PROFILE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PROFILE = "profile"
    # 枚举说明：METRICS 是该枚举允许出现的一个业务取值。
    METRICS = "metrics"
    # 枚举说明：REPORTS 是该枚举允许出现的一个业务取值。
    REPORTS = "reports"
    # 枚举说明：SYMPTOMS 是该枚举允许出现的一个业务取值。
    SYMPTOMS = "symptoms"
    # 枚举说明：MEDICAL_EVENTS 是该枚举允许出现的一个业务取值。
    MEDICAL_EVENTS = "medical_events"
    # 枚举说明：DOCUMENTS 是该枚举允许出现的一个业务取值。
    DOCUMENTS = "documents"
    # 枚举说明：ALERTS 是该枚举允许出现的一个业务取值。
    ALERTS = "alerts"
    # 枚举说明：MEMORY_SUMMARY 是该枚举允许出现的一个业务取值。
    MEMORY_SUMMARY = "memory_summary"
    # 枚举说明：AUDIT 是该枚举允许出现的一个业务取值。
    AUDIT = "audit"


# 类职责：DataAccessAction 约束 审计模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DataAccessAction(StrEnum):
    # 枚举说明：VIEW 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    VIEW = "view"
    # 枚举说明：CREATE 是该枚举允许出现的一个业务取值。
    CREATE = "create"
    # 枚举说明：UPDATE 是该枚举允许出现的一个业务取值。
    UPDATE = "update"
    # 枚举说明：DELETE 是该枚举允许出现的一个业务取值。
    DELETE = "delete"
    # 枚举说明：GENERATE 是该枚举允许出现的一个业务取值。
    GENERATE = "generate"
    # 枚举说明：EXPORT 是该枚举允许出现的一个业务取值。
    EXPORT = "export"


# 类职责：PrivacyEventType 约束 审计模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class PrivacyEventType(StrEnum):
    # 枚举说明：PERMISSION_UPDATED 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PERMISSION_UPDATED = "permission_updated"
    # 枚举说明：DOCUMENT_UPLOADED 是该枚举允许出现的一个业务取值。
    DOCUMENT_UPLOADED = "document_uploaded"
    # 枚举说明：DOCUMENT_DELETED 是该枚举允许出现的一个业务取值。
    DOCUMENT_DELETED = "document_deleted"
    # 枚举说明：DATA_EXPORTED 是该枚举允许出现的一个业务取值。
    DATA_EXPORTED = "data_exported"
    # 枚举说明：SHARE_LINK_CREATED 是该枚举允许出现的一个业务取值。
    SHARE_LINK_CREATED = "share_link_created"
    # 枚举说明：SHARE_LINK_REVOKED 是该枚举允许出现的一个业务取值。
    SHARE_LINK_REVOKED = "share_link_revoked"
    # 枚举说明：AGENT_ACCESSED_DATA 是该枚举允许出现的一个业务取值。
    AGENT_ACCESSED_DATA = "agent_accessed_data"
    # 枚举说明：USER_DELETED_DATA 是该枚举允许出现的一个业务取值。
    USER_DELETED_DATA = "user_deleted_data"
    # 枚举说明：ACCOUNT_DELETED 是该枚举允许出现的一个业务取值。
    ACCOUNT_DELETED = "account_deleted"
