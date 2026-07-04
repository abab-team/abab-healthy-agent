from __future__ import annotations

from typing import TYPE_CHECKING

from app.agent.tools.alert_tools import ActiveAlertsListTool
from app.agent.tools.base import AgentTool
from app.agent.tools.health_data_tools import BloodPressureSummaryTool
from app.agent.tools.health_profile_tools import HealthProfileGetTool
from app.agent.tools.health_record_tools import SymptomsSummaryTool
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


__all__ = [
    "ActiveAlertsListTool",
    "AgentTool",
    "BloodPressureSummaryTool",
    "HealthProfileGetTool",
    "MedicalFollowupsListTool",
    "SymptomsSummaryTool",
    "register_readonly_health_tools",
]
