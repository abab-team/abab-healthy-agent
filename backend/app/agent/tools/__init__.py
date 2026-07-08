from __future__ import annotations

from typing import TYPE_CHECKING

from app.agent.tools.alert_tools import ActiveAlertsListTool, AlertCreateTool, AlertsQueryTool
from app.agent.tools.base import AgentTool
from app.agent.tools.document_tools import DocumentsQueryTool, MedicalEventDraftCreateTool
from app.agent.tools.health_data_tools import BloodPressureSummaryTool, MetricSummaryTool, RecentMetricsTool
from app.agent.tools.health_profile_tools import HealthProfileGetTool
from app.agent.tools.health_record_tools import SymptomDraftCreateTool, SymptomsQueryTool, SymptomsSummaryTool
from app.agent.tools.medical_timeline_tools import MedicalEventsQueryTool, MedicalFollowupsListTool

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


def register_health_query_tools(registry: AgentToolRegistry) -> AgentToolRegistry:
    register_readonly_health_tools(registry)
    registry.register(MetricSummaryTool())
    registry.register(RecentMetricsTool())
    registry.register(SymptomsQueryTool())
    registry.register(MedicalEventsQueryTool())
    registry.register(DocumentsQueryTool())
    registry.register(AlertsQueryTool())
    return registry


__all__ = [
    "ActiveAlertsListTool",
    "AlertCreateTool",
    "AlertsQueryTool",
    "AgentTool",
    "BloodPressureSummaryTool",
    "DocumentsQueryTool",
    "HealthProfileGetTool",
    "MedicalEventDraftCreateTool",
    "MedicalEventsQueryTool",
    "MedicalFollowupsListTool",
    "MetricSummaryTool",
    "RecentMetricsTool",
    "SymptomDraftCreateTool",
    "SymptomsQueryTool",
    "SymptomsSummaryTool",
    "register_health_query_tools",
    "register_readonly_health_tools",
    "register_write_draft_tools",
]
