# 模块领域：Agent 工作流层
# 领域说明：负责串联意图解析、权限校验、工具调用、结果汇总和安全输出。
# 文件职责：工作流文件。编排多步骤业务流程，把权限、工具、规则和输出串起来。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from typing import Any

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_health_query_tools
from app.core.config import get_settings


WORKFLOW_TYPE = "document_extract_workflow"


class DocumentExtractWorkflow:
    workflow_name = AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW

    def __init__(self, executor: AgentToolExecutor | None = None, *, settings=None) -> None:
        if executor is None:
            executor = AgentToolExecutor(register_health_query_tools(AgentToolRegistry()))
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.document_extract_graph import DocumentExtractGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            DocumentExtractGraph(workflow=self),
            lambda: run_document_extract_workflow(context, executor=self.executor),
        )

    def call_documents_query(self, context: AgentWorkflowContext) -> ToolExecutionResult:
        payload = context.request.workflow_payload or {}
        return self.executor.execute(
            context.db,
            ToolExecutionRequest(
                trace_id=context.trace_id,
                tool_name="documents.query",
                actor_user_id=context.request.actor_user_id,
                target_user_id=context.request.target_user_id,
                family_id=context.request.family_id,
                input_data={"limit": 1, "document_id": str(payload.get("document_id") or "")[:80]},
                confirmed=False,
                safety_level=context.safety_level,
                reason=WORKFLOW_TYPE,
            ),
        )


def run_document_extract_workflow(context: AgentWorkflowContext, *, executor: AgentToolExecutor) -> AgentWorkflowResult:
    workflow = DocumentExtractWorkflow(executor=executor)
    tool_result = workflow.call_documents_query(context)
    return build_document_extract_result(context, tool_result)


def build_document_extract_result(context: AgentWorkflowContext, tool_result: ToolExecutionResult) -> AgentWorkflowResult:
    payload = context.request.workflow_payload or {}
    file_name = _safe_label(payload.get("file_name") or "uploaded document")
    mime_type = _safe_label(payload.get("mime_type") or "unknown")
    if tool_result.blocked or tool_result.status != "completed":
        content = (
            "Based on system records only, this document extraction preview is unavailable because of permissions "
            "or missing document metadata. No raw OCR text, file path, or formal health fact is returned. "
            "This does not replace a doctor's judgment."
        )
        return AgentWorkflowResult(message="Document extraction preview unavailable.", generated_content=content, tool_calls_count=1)
    content = (
        "Based on system records only, a document extraction preview package was generated. "
        f"file_name={file_name}; mime_type={mime_type}; "
        "summary_candidate=metadata-only preview; medical_event_draft_candidate=pending user confirmation; "
        "raw_ocr_returned=false; file_path_returned=false; formal_health_fact_created=false. "
        "This package only organizes uploaded material and does not replace a doctor's judgment."
    )
    return AgentWorkflowResult(message="Document extraction preview generated.", generated_content=content, tool_calls_count=1)


def _safe_label(value: Any) -> str:
    text = str(value or "").replace("\\", "/")
    for marker in ("file://", "../", "token", "password", "api_key", "private_key"):
        text = text.replace(marker, "[redacted]")
    return text[:120]
