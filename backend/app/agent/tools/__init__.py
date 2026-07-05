from __future__ import annotations

from typing import TYPE_CHECKING

from app.agent.tools.alert_tools import ActiveAlertsListTool, AlertCreateTool
from app.agent.tools.base import AgentTool
from app.agent.tools.document_tools import MedicalEventDraftCreateTool
from app.agent.tools.health_data_tools import BloodPressureSummaryTool
from app.agent.tools.health_profile_tools import HealthProfileGetTool
from app.agent.tools.health_record_tools import SymptomDraftCreateTool, SymptomsSummaryTool
from app.agent.tools.medical_timeline_tools import MedicalFollowupsListTool

if TYPE_CHECKING:
    from app.agent.tool_registry import AgentToolRegistry


def register_readonly_health_tools(registry: AgentToolRegistry) -> AgentToolRegistry:
    registry.register(HealthProfileGetTool())
    registry.register(BloodPressureSummaryTool())
    registry.register(SymptomsSummaryTool())
    registry.register(MedicalFollowupsListTool())
    registry.register(ActiveAlertsListTool())
    return registry


def register_write_draft_tools(registry: AgentToolRegistry) -> AgentToolRegistry:
    registry.register(SymptomDraftCreateTool())
    registry.register(MedicalEventDraftCreateTool())
    registry.register(AlertCreateTool())
    return registry


__all__ = [
    "ActiveAlertsListTool",
    "AlertCreateTool",
    "AgentTool",
    "BloodPressureSummaryTool",
    "HealthProfileGetTool",
    "MedicalEventDraftCreateTool",
    "MedicalFollowupsListTool",
    "SymptomDraftCreateTool",
    "SymptomsSummaryTool",
    "register_readonly_health_tools",
    "register_write_draft_tools",
]
