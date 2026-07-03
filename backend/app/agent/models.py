from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.agent.enums import (
    AgentMemorySource,
    AgentMemoryStatus,
    AgentMemoryType,
    AgentMemoryVisibility,
    AgentSafetyLevel,
    AgentToolAccessMode,
    AgentToolCallStatus,
    AgentToolRiskLevel,
    AgentTraceStatus,
    AgentTriggerType,
    AgentWorkflowName,
)
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.health_data.enums import ConfidenceLevel


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class AgentTrace(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_traces"

    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    trigger_type: Mapped[AgentTriggerType] = mapped_column(
        Enum(
            AgentTriggerType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    current_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_page: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AgentTraceStatus] = mapped_column(
        Enum(
            AgentTraceStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AgentTraceStatus.RUNNING,
    )
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agent_traces_request_id", "request_id", unique=True),
        Index("ix_agent_traces_session_id", "session_id"),
        Index("ix_agent_traces_workflow_name", "workflow_name"),
        Index("ix_agent_traces_trigger_type", "trigger_type"),
        Index("ix_agent_traces_current_user_id", "current_user_id"),
        Index("ix_agent_traces_current_family_id", "current_family_id"),
        Index("ix_agent_traces_target_user_id", "target_user_id"),
        Index("ix_agent_traces_status", "status"),
        Index("ix_agent_traces_started_at", "started_at"),
        Index("ix_agent_traces_created_at", "created_at"),
    )


class AgentToolCall(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_tool_calls"

    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    access_mode: Mapped[AgentToolAccessMode] = mapped_column(
        Enum(
            AgentToolAccessMode,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    risk_level: Mapped[AgentToolRiskLevel] = mapped_column(
        Enum(
            AgentToolRiskLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    current_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    permission_checked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    permission_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    input_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[AgentToolCallStatus] = mapped_column(
        Enum(
            AgentToolCallStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agent_tool_calls_request_id", "request_id"),
        Index("ix_agent_tool_calls_workflow_name", "workflow_name"),
        Index("ix_agent_tool_calls_tool_name", "tool_name"),
        Index("ix_agent_tool_calls_access_mode", "access_mode"),
        Index("ix_agent_tool_calls_risk_level", "risk_level"),
        Index("ix_agent_tool_calls_current_user_id", "current_user_id"),
        Index("ix_agent_tool_calls_target_user_id", "target_user_id"),
        Index("ix_agent_tool_calls_permission_checked", "permission_checked"),
        Index("ix_agent_tool_calls_status", "status"),
        Index("ix_agent_tool_calls_created_at", "created_at"),
    )


class AgentSafetyCheck(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_safety_checks"

    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    safety_level: Mapped[AgentSafetyLevel] = mapped_column(
        Enum(
            AgentSafetyLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    was_rewritten: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_answer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    revised_answer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agent_safety_checks_request_id", "request_id"),
        Index("ix_agent_safety_checks_workflow_name", "workflow_name"),
        Index("ix_agent_safety_checks_intent", "intent"),
        Index("ix_agent_safety_checks_safety_level", "safety_level"),
        Index("ix_agent_safety_checks_passed", "passed"),
        Index("ix_agent_safety_checks_was_rewritten", "was_rewritten"),
        Index("ix_agent_safety_checks_created_at", "created_at"),
    )


class AgentMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_memories"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_type: Mapped[AgentMemoryType] = mapped_column(
        Enum(
            AgentMemoryType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[AgentMemorySource] = mapped_column(
        Enum(
            AgentMemorySource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    source_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(
            ConfidenceLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ConfidenceLevel.UNKNOWN,
    )
    visibility: Mapped[AgentMemoryVisibility] = mapped_column(
        Enum(
            AgentMemoryVisibility,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AgentMemoryVisibility.PRIVATE,
    )
    status: Mapped[AgentMemoryStatus] = mapped_column(
        Enum(
            AgentMemoryStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AgentMemoryStatus.ACTIVE,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_agent_memories_user_id", "user_id"),
        Index("ix_agent_memories_family_id", "family_id"),
        Index("ix_agent_memories_target_user_id", "target_user_id"),
        Index("ix_agent_memories_memory_type", "memory_type"),
        Index("ix_agent_memories_source", "source"),
        Index("ix_agent_memories_confidence_level", "confidence_level"),
        Index("ix_agent_memories_visibility", "visibility"),
        Index("ix_agent_memories_status", "status"),
        Index("ix_agent_memories_last_used_at", "last_used_at"),
        Index("ix_agent_memories_expires_at", "expires_at"),
        Index("ix_agent_memories_created_at", "created_at"),
    )
