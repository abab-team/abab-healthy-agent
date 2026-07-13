from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentWorkflowName


MAX_AGENT_USER_MESSAGE_LENGTH = 2000
AgentToolCategory = Literal[
    "health_profile",
    "health_data",
    "health_record",
    "medical_timeline",
    "document",
    "report",
    "alert",
    "system",
]
AgentToolAccessMode = Literal["none", "read", "write", "draft", "admin"]
AgentToolRiskLevel = Literal["low", "medium", "high", "critical"]
AgentSafetyCategory = Literal[
    "general",
    "record_keeping",
    "health_summary",
    "medical_question",
    "diagnosis_request",
    "prescription_request",
    "dosage_request",
    "medication_change_request",
    "emergency_symptom",
    "mental_health_crisis",
    "self_harm",
    "unknown",
]
AgentSafetyDecisionLevel = Literal["safe", "caution", "high_risk", "emergency", "blocked"]


@dataclass(frozen=True)
class AgentRunRequest:
    actor_user_id: UUID
    target_user_id: UUID
    workflow_type: AgentWorkflowName | str
    user_message: str
    family_id: UUID | None = None
    source: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    confirmation: bool = False
    workflow_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class AgentRunResult:
    trace_id: UUID | None
    status: str
    workflow_type: str
    message: str
    blocked: bool
    safety_level: str
    tool_calls_count: int = 0
    generated_content: str | None = None
    session_id: str | None = None
    suggested_action: str | None = None


@dataclass(frozen=True)
class AgentWorkflowResult:
    message: str
    generated_content: str | None = None
    status: AgentTraceStatus = AgentTraceStatus.SUCCESS
    tool_calls_count: int = 0
    suggested_action: str | None = None


@dataclass(frozen=True)
class AgentWorkflowContext:
    db: Session
    trace_id: UUID
    request: AgentRunRequest
    safety_level: str


@dataclass(frozen=True)
class AgentSafetyResult:
    passed: bool
    safety_level: AgentSafetyLevel
    flags: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    input_risk_summary: str | None = None


@dataclass(frozen=True)
class AgentSafetyDecision:
    allowed: bool
    blocked: bool
    safety_level: AgentSafetyDecisionLevel
    category: AgentSafetyCategory
    reason_code: str
    safe_message: str
    requires_human_review: bool = False
    requires_medical_attention: bool = False
    disallowed_actions: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    matched_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentTraceStart:
    request_id: str
    workflow_name: AgentWorkflowName
    current_user_id: UUID
    target_user_id: UUID | None
    current_family_id: UUID | None = None
    session_id: str | None = None
    source_page: str | None = None
    raw_input_summary: str | None = None


@dataclass(frozen=True)
class AgentToolMetadata:
    name: str
    description: str
    category: AgentToolCategory
    access_mode: AgentToolAccessMode
    risk_level: AgentToolRiskLevel
    required_permission_type: str | None = None
    required_permission_action: str | None = None
    requires_confirmation: bool = False
    enabled: bool = True
    input_schema_name: str | None = None
    output_schema_name: str | None = None
    safety_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolExecutionRequest:
    trace_id: UUID
    tool_name: str
    actor_user_id: UUID
    target_user_id: UUID
    input_data: dict
    family_id: UUID | None = None
    confirmed: bool = False
    safety_level: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    status: str
    blocked: bool
    requires_confirmation: bool
    message: str
    output_data: dict | None = None
    tool_call_id: UUID | None = None
    error_code: str | None = None
