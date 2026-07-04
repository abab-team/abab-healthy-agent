from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentWorkflowName


MAX_AGENT_USER_MESSAGE_LENGTH = 2000


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


@dataclass(frozen=True)
class AgentWorkflowResult:
    message: str
    generated_content: str | None = None
    status: AgentTraceStatus = AgentTraceStatus.SUCCESS
    tool_calls_count: int = 0


@dataclass(frozen=True)
class AgentSafetyResult:
    passed: bool
    safety_level: AgentSafetyLevel
    flags: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    input_risk_summary: str | None = None


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
