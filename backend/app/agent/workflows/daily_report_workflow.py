# 模块领域：Agent 工作流层
# 领域说明：负责串联意图解析、权限校验、工具调用、结果汇总和安全输出。
# 文件职责：工作流文件。编排多步骤业务流程，把权限、工具、规则和输出串起来。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult
from app.agent.workflows.daily_health_brief import DailyHealthBriefWorkflow
from app.core.config import get_settings


class DailyReportWorkflow:
    workflow_name = AgentWorkflowName.DAILY_REPORT_WORKFLOW

    def __init__(self, *, settings=None, daily_brief_workflow: DailyHealthBriefWorkflow | None = None) -> None:
        self.settings = settings or get_settings()
        self.daily_brief_workflow = daily_brief_workflow or DailyHealthBriefWorkflow(settings=self.settings)
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.daily_report_graph import DailyReportGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            DailyReportGraph(workflow=self),
            lambda: run_daily_report_workflow(context, daily_brief_workflow=self.daily_brief_workflow),
        )


def run_daily_report_workflow(
    context: AgentWorkflowContext,
    *,
    daily_brief_workflow: DailyHealthBriefWorkflow,
) -> AgentWorkflowResult:
    brief = daily_brief_workflow.run(context)
    content = (
        "Based on system records only, a daily report preview was generated. "
        "No stored daily report was created in this workflow. "
        f"readonly_tool_calls={brief.tool_calls_count}; "
        "The preview organizes available system record sections and does not replace clinician review."
    )
    return AgentWorkflowResult(
        message="Daily report preview generated from system records.",
        generated_content=content,
        tool_calls_count=brief.tool_calls_count,
    )
