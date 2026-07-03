# 模块领域：健康 Agent 核心层
# 领域说明：负责运行时上下文、工具调用、工作流编排、安全边界和执行审计。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：AgentWorkflowName 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentWorkflowName(StrEnum):
    # 枚举说明：CHAT_WORKFLOW 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    CHAT_WORKFLOW = "chat_workflow"
    # 枚举说明：FREE_TEXT_RECORD_WORKFLOW 是该枚举允许出现的一个业务取值。
    FREE_TEXT_RECORD_WORKFLOW = "free_text_record_workflow"
    # 枚举说明：DOCUMENT_EXTRACT_WORKFLOW 是该枚举允许出现的一个业务取值。
    DOCUMENT_EXTRACT_WORKFLOW = "document_extract_workflow"
    # 枚举说明：DAILY_REPORT_WORKFLOW 是该枚举允许出现的一个业务取值。
    DAILY_REPORT_WORKFLOW = "daily_report_workflow"
    # 枚举说明：DOCTOR_VISIT_SUMMARY_WORKFLOW 是该枚举允许出现的一个业务取值。
    DOCTOR_VISIT_SUMMARY_WORKFLOW = "doctor_visit_summary_workflow"
    # 枚举说明：HEALTH_KNOWLEDGE_QA_WORKFLOW 是该枚举允许出现的一个业务取值。
    HEALTH_KNOWLEDGE_QA_WORKFLOW = "health_knowledge_qa_workflow"


# 类职责：AgentTriggerType 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentTriggerType(StrEnum):
    # 枚举说明：USER_CHAT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    USER_CHAT = "user_chat"
    # 枚举说明：FREE_TEXT_RECORD 是该枚举允许出现的一个业务取值。
    FREE_TEXT_RECORD = "free_text_record"
    # 枚举说明：DOCUMENT_UPLOAD 是该枚举允许出现的一个业务取值。
    DOCUMENT_UPLOAD = "document_upload"
    # 枚举说明：MANUAL_REPORT_GENERATE 是该枚举允许出现的一个业务取值。
    MANUAL_REPORT_GENERATE = "manual_report_generate"
    # 枚举说明：SCHEDULED_REPORT_GENERATE 是该枚举允许出现的一个业务取值。
    SCHEDULED_REPORT_GENERATE = "scheduled_report_generate"
    # 枚举说明：DOCTOR_VISIT_SUMMARY 是该枚举允许出现的一个业务取值。
    DOCTOR_VISIT_SUMMARY = "doctor_visit_summary"
    # 枚举说明：SYSTEM_JOB 是该枚举允许出现的一个业务取值。
    SYSTEM_JOB = "system_job"


# 类职责：AgentTraceStatus 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentTraceStatus(StrEnum):
    # 枚举说明：RUNNING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    RUNNING = "running"
    # 枚举说明：SUCCESS 是该枚举允许出现的一个业务取值。
    SUCCESS = "success"
    # 枚举说明：PARTIAL_SUCCESS 是该枚举允许出现的一个业务取值。
    PARTIAL_SUCCESS = "partial_success"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"
    # 枚举说明：BLOCKED 是该枚举允许出现的一个业务取值。
    BLOCKED = "blocked"
    # 枚举说明：PERMISSION_DENIED 是该枚举允许出现的一个业务取值。
    PERMISSION_DENIED = "permission_denied"
    # 枚举说明：CANCELLED 是该枚举允许出现的一个业务取值。
    CANCELLED = "cancelled"


# 类职责：AgentToolAccessMode 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentToolAccessMode(StrEnum):
    # 枚举说明：READ 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    READ = "read"
    # 枚举说明：WRITE 是该枚举允许出现的一个业务取值。
    WRITE = "write"
    # 枚举说明：DRAFT 是该枚举允许出现的一个业务取值。
    DRAFT = "draft"
    # 枚举说明：CONTROL 是该枚举允许出现的一个业务取值。
    CONTROL = "control"


# 类职责：AgentToolRiskLevel 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentToolRiskLevel(StrEnum):
    # 枚举说明：LOW 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    LOW = "low"
    # 枚举说明：MEDIUM 是该枚举允许出现的一个业务取值。
    MEDIUM = "medium"
    # 枚举说明：HIGH 是该枚举允许出现的一个业务取值。
    HIGH = "high"
    # 枚举说明：CRITICAL 是该枚举允许出现的一个业务取值。
    CRITICAL = "critical"


# 类职责：AgentToolCallStatus 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentToolCallStatus(StrEnum):
    # 枚举说明：SUCCESS 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SUCCESS = "success"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"
    # 枚举说明：SKIPPED 是该枚举允许出现的一个业务取值。
    SKIPPED = "skipped"
    # 枚举说明：BLOCKED_BY_PERMISSION 是该枚举允许出现的一个业务取值。
    BLOCKED_BY_PERMISSION = "blocked_by_permission"
    # 枚举说明：BLOCKED_BY_REGISTRY 是该枚举允许出现的一个业务取值。
    BLOCKED_BY_REGISTRY = "blocked_by_registry"
    # 枚举说明：BLOCKED_BY_GUARD 是该枚举允许出现的一个业务取值。
    BLOCKED_BY_GUARD = "blocked_by_guard"
    # 枚举说明：TIMEOUT 是该枚举允许出现的一个业务取值。
    TIMEOUT = "timeout"


# 类职责：AgentSafetyLevel 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentSafetyLevel(StrEnum):
    # 枚举说明：SAFE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SAFE = "safe"
    # 枚举说明：CAUTION 是该枚举允许出现的一个业务取值。
    CAUTION = "caution"
    # 枚举说明：HIGH_RISK 是该枚举允许出现的一个业务取值。
    HIGH_RISK = "high_risk"
    # 枚举说明：BLOCKED 是该枚举允许出现的一个业务取值。
    BLOCKED = "blocked"


# 类职责：AgentMemoryType 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentMemoryType(StrEnum):
    # 枚举说明：USER_PREFERENCE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    USER_PREFERENCE = "user_preference"
    # 枚举说明：ATTENTION_FOCUS 是该枚举允许出现的一个业务取值。
    ATTENTION_FOCUS = "attention_focus"
    # 枚举说明：CONVERSATION_SUMMARY 是该枚举允许出现的一个业务取值。
    CONVERSATION_SUMMARY = "conversation_summary"
    # 枚举说明：HEALTH_SUMMARY_INDEX 是该枚举允许出现的一个业务取值。
    HEALTH_SUMMARY_INDEX = "health_summary_index"
    # 枚举说明：WORKFLOW_PREFERENCE 是该枚举允许出现的一个业务取值。
    WORKFLOW_PREFERENCE = "workflow_preference"


# 类职责：AgentMemorySource 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentMemorySource(StrEnum):
    # 枚举说明：USER_INPUT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    USER_INPUT = "user_input"
    # 枚举说明：WORKFLOW 是该枚举允许出现的一个业务取值。
    WORKFLOW = "workflow"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"
    # 枚举说明：MANUAL 是该枚举允许出现的一个业务取值。
    MANUAL = "manual"


# 类职责：AgentMemoryVisibility 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentMemoryVisibility(StrEnum):
    # 枚举说明：PRIVATE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PRIVATE = "private"
    # 枚举说明：FAMILY_CONTEXT 是该枚举允许出现的一个业务取值。
    FAMILY_CONTEXT = "family_context"


# 类职责：AgentMemoryStatus 约束 健康 Agent 核心层 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AgentMemoryStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：ARCHIVED 是该枚举允许出现的一个业务取值。
    ARCHIVED = "archived"
    # 枚举说明：DELETED 是该枚举允许出现的一个业务取值。
    DELETED = "deleted"
    # 枚举说明：EXPIRED 是该枚举允许出现的一个业务取值。
    EXPIRED = "expired"
