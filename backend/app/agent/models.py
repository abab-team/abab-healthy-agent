# 模块领域：健康 Agent 核心层
# 领域说明：负责运行时上下文、工具调用、工作流编排、安全边界和执行审计。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：业务函数，封装 健康 Agent 核心层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：AgentTrace 是 健康 Agent 核心层 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class AgentTrace(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "agent_traces"

    # 字段说明：request_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # 字段说明：session_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：workflow_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：trigger_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    trigger_type: Mapped[AgentTriggerType] = mapped_column(
        Enum(
            AgentTriggerType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：current_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    current_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：current_family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    current_family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：source_page 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source_page: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：raw_input_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    raw_input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：final_output_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    final_output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：error_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：error_message 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：started_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：ended_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：duration_ms 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：AgentToolCall 是 健康 Agent 核心层 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class AgentToolCall(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "agent_tool_calls"

    # 字段说明：request_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # 字段说明：workflow_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：tool_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 字段说明：access_mode 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    access_mode: Mapped[AgentToolAccessMode] = mapped_column(
        Enum(
            AgentToolAccessMode,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：risk_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    risk_level: Mapped[AgentToolRiskLevel] = mapped_column(
        Enum(
            AgentToolRiskLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：current_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    current_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：permission_checked 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    permission_checked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：permission_result 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    permission_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：input_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    input_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：output_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    output_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[AgentToolCallStatus] = mapped_column(
        Enum(
            AgentToolCallStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：error_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：error_message 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：duration_ms 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：AgentSafetyCheck 是 健康 Agent 核心层 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class AgentSafetyCheck(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "agent_safety_checks"

    # 字段说明：request_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # 字段说明：workflow_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    workflow_name: Mapped[AgentWorkflowName] = mapped_column(
        Enum(
            AgentWorkflowName,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：intent 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：safety_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    safety_level: Mapped[AgentSafetyLevel] = mapped_column(
        Enum(
            AgentSafetyLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：safety_flags 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：passed 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # 字段说明：was_rewritten 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    was_rewritten: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：blocked_reason 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：input_risk_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    input_risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：original_answer_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    original_answer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：revised_answer_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    revised_answer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：AgentMemory 是 健康 Agent 核心层 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class AgentMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "agent_memories"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：memory_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    memory_type: Mapped[AgentMemoryType] = mapped_column(
        Enum(
            AgentMemoryType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：content 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[AgentMemorySource] = mapped_column(
        Enum(
            AgentMemorySource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：source_entity_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：source_entity_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source_entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：confidence_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：visibility 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：last_used_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


class AgentSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agent_sessions_user_id", "user_id"),
        Index("ix_agent_sessions_family_id", "family_id"),
        Index("ix_agent_sessions_last_active_at", "last_active_at"),
        Index("ix_agent_sessions_created_at", "created_at"),
    )


class AgentMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_messages"

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content_summary: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    member_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    member_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metric_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_range_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_range_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_agent_messages_session_id", "session_id"),
        Index("ix_agent_messages_role", "role"),
        Index("ix_agent_messages_intent", "intent"),
        Index("ix_agent_messages_target_user_id", "target_user_id"),
        Index("ix_agent_messages_metric_type", "metric_type"),
        Index("ix_agent_messages_created_at", "created_at"),
    )
