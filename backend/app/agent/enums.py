from enum import StrEnum


class AgentWorkflowName(StrEnum):
    CHAT_WORKFLOW = "chat_workflow"
    FREE_TEXT_RECORD_WORKFLOW = "free_text_record_workflow"
    DOCUMENT_EXTRACT_WORKFLOW = "document_extract_workflow"
    DAILY_REPORT_WORKFLOW = "daily_report_workflow"
    DOCTOR_VISIT_SUMMARY_WORKFLOW = "doctor_visit_summary_workflow"
    HEALTH_KNOWLEDGE_QA_WORKFLOW = "health_knowledge_qa_workflow"


class AgentTriggerType(StrEnum):
    USER_CHAT = "user_chat"
    FREE_TEXT_RECORD = "free_text_record"
    DOCUMENT_UPLOAD = "document_upload"
    MANUAL_REPORT_GENERATE = "manual_report_generate"
    SCHEDULED_REPORT_GENERATE = "scheduled_report_generate"
    DOCTOR_VISIT_SUMMARY = "doctor_visit_summary"
    SYSTEM_JOB = "system_job"


class AgentTraceStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    BLOCKED = "blocked"
    PERMISSION_DENIED = "permission_denied"
    CANCELLED = "cancelled"


class AgentToolAccessMode(StrEnum):
    READ = "read"
    WRITE = "write"
    DRAFT = "draft"
    CONTROL = "control"


class AgentToolRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentToolCallStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED_BY_PERMISSION = "blocked_by_permission"
    BLOCKED_BY_REGISTRY = "blocked_by_registry"
    BLOCKED_BY_GUARD = "blocked_by_guard"
    TIMEOUT = "timeout"


class AgentSafetyLevel(StrEnum):
    SAFE = "safe"
    CAUTION = "caution"
    HIGH_RISK = "high_risk"
    BLOCKED = "blocked"


class AgentMemoryType(StrEnum):
    USER_PREFERENCE = "user_preference"
    ATTENTION_FOCUS = "attention_focus"
    CONVERSATION_SUMMARY = "conversation_summary"
    HEALTH_SUMMARY_INDEX = "health_summary_index"
    WORKFLOW_PREFERENCE = "workflow_preference"


class AgentMemorySource(StrEnum):
    USER_INPUT = "user_input"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    MANUAL = "manual"


class AgentMemoryVisibility(StrEnum):
    PRIVATE = "private"
    FAMILY_CONTEXT = "family_context"


class AgentMemoryStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"
