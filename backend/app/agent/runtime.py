from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.agent import safety, service
from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentWorkflowName
from app.agent.exceptions import AgentRuntimeError, AgentWorkflowNotRegisteredError
from app.agent.schemas import AgentRunRequest, AgentRunResult
from app.agent.workflows import AgentWorkflowRegistry, default_workflow_registry


SAFE_FAILED_MESSAGE = "Agent runtime could not execute this workflow safely in the current phase."
SAFE_BLOCKED_MESSAGE = "Agent runtime blocked this request before workflow execution."


class AgentRuntime:
    def __init__(self, registry: AgentWorkflowRegistry | None = None) -> None:
        self.registry = registry or default_workflow_registry()

    def run(self, db: Session, request: AgentRunRequest) -> AgentRunResult:
        request_id = request.request_id or str(uuid4())
        workflow_name, requested_workflow = _coerce_workflow_name(request.workflow_type)
        trace = service.start_trace(
            db,
            request_id=request_id,
            workflow_name=workflow_name,
            current_user_id=request.actor_user_id,
            current_family_id=request.family_id,
            target_user_id=request.target_user_id,
            session_id=request.session_id,
            source_page=safety.excerpt_text(request.source, max_length=100),
            raw_input_summary=_input_summary(request.user_message, requested_workflow),
        )
        try:
            safety_result = safety.check_user_message(request.user_message)
            service.record_safety_check(
                db,
                request_id=request_id,
                workflow_name=workflow_name,
                safety_level=safety_result.safety_level,
                passed=safety_result.passed,
                safety_flags=safety_result.flags,
                blocked_reason=safety_result.blocked_reason,
                input_risk_summary=safety_result.input_risk_summary,
            )
            if not safety_result.passed:
                service.fail_trace(
                    db,
                    trace.id,
                    error_type="safety_blocked",
                    error_message=safety_result.blocked_reason or "safety blocked",
                    final_output_summary=SAFE_BLOCKED_MESSAGE,
                    status=AgentTraceStatus.BLOCKED,
                )
                db.commit()
                return AgentRunResult(
                    trace_id=trace.id,
                    status="blocked",
                    workflow_type=requested_workflow,
                    message=SAFE_BLOCKED_MESSAGE,
                    blocked=True,
                    safety_level=safety_result.safety_level.value,
                    generated_content=None,
                )

            handler = self.registry.get(workflow_name)
            workflow_result = handler.run(request)
            service.complete_trace(db, trace.id, final_output_summary=safety.excerpt_text(workflow_result.message))
            db.commit()
            return AgentRunResult(
                trace_id=trace.id,
                status="completed",
                workflow_type=workflow_name.value,
                message=workflow_result.message,
                blocked=False,
                safety_level=safety_result.safety_level.value,
                tool_calls_count=workflow_result.tool_calls_count,
                generated_content=workflow_result.generated_content,
            )
        except AgentWorkflowNotRegisteredError as exc:
            service.fail_trace(
                db,
                trace.id,
                error_type=exc.__class__.__name__,
                error_message="workflow handler is not registered",
                final_output_summary=SAFE_FAILED_MESSAGE,
            )
            db.commit()
            return _failed_result(trace.id, requested_workflow, AgentSafetyLevel.SAFE)
        except Exception as exc:
            service.fail_trace(
                db,
                trace.id,
                error_type=exc.__class__.__name__,
                error_message="agent workflow failed",
                final_output_summary=SAFE_FAILED_MESSAGE,
            )
            db.commit()
            return _failed_result(trace.id, requested_workflow, AgentSafetyLevel.SAFE)


AgentHarness = AgentRuntime


def _coerce_workflow_name(workflow_type: AgentWorkflowName | str) -> tuple[AgentWorkflowName, str]:
    if isinstance(workflow_type, AgentWorkflowName):
        return workflow_type, workflow_type.value
    requested = str(workflow_type)
    try:
        return AgentWorkflowName(requested), requested
    except ValueError:
        return AgentWorkflowName.CHAT_WORKFLOW, requested


def _input_summary(user_message: str, workflow_type: str) -> str:
    excerpt = safety.excerpt_text(user_message, max_length=200) or ""
    return f"workflow={workflow_type}; length={len(user_message)}; excerpt={excerpt}"


def _failed_result(trace_id, workflow_type: str, safety_level: AgentSafetyLevel) -> AgentRunResult:
    return AgentRunResult(
        trace_id=trace_id,
        status="failed",
        workflow_type=workflow_type,
        message=SAFE_FAILED_MESSAGE,
        blocked=True,
        safety_level=safety_level.value,
        tool_calls_count=0,
        generated_content=None,
    )
