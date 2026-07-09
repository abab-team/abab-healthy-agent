# 模块领域：Agent 工作流层
# 领域说明：负责串联意图解析、权限校验、工具调用、结果汇总和安全输出。
# 文件职责：工作流文件。编排多步骤业务流程，把权限、工具、规则和输出串起来。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult
from app.core.config import get_settings
from app.rag.context import safe_rag_context_for_agent


class HealthKnowledgeQAWorkflow:
    workflow_name = AgentWorkflowName.HEALTH_KNOWLEDGE_QA_WORKFLOW

    def __init__(self, *, settings=None) -> None:
        self.settings = settings or get_settings()
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.health_knowledge_qa_graph import HealthKnowledgeQAGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            HealthKnowledgeQAGraph(settings=self.settings),
            lambda: run_health_knowledge_qa(context, settings=self.settings),
        )


def run_health_knowledge_qa(context: AgentWorkflowContext, *, settings=None) -> AgentWorkflowResult:
    _, lines, fallback_reason = safe_rag_context_for_agent(
        context.db,
        current_user_id=context.request.actor_user_id,
        target_user_id=context.request.target_user_id,
        family_id=context.request.family_id,
        query=context.request.user_message,
        top_k=3,
        settings=settings,
    )
    if lines:
        source_lines = "\n".join(f"- {line}" for line in lines)
        content = (
            "Based on system records only, here are safe internal record excerpts related to your question:\n"
            f"{source_lines}\n"
            "This answer organizes system information and does not replace a doctor's judgment."
        )
    else:
        reason = fallback_reason or "no_internal_sources"
        content = (
            "Based on system records only, no safe internal source was available for this question. "
            f"fallback_reason={reason}. "
            "This workflow does not use external medical knowledge and does not replace a doctor's judgment."
        )
    return AgentWorkflowResult(
        message="Health knowledge QA response generated from safe internal context.",
        generated_content=content,
        tool_calls_count=0,
    )
