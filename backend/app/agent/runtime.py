from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.agent import safety, service
from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentWorkflowName
from app.agent.exceptions import AgentRuntimeError, AgentWorkflowNotRegisteredError
from app.agent.schemas import AgentRunRequest, AgentRunResult, AgentWorkflowContext
from app.agent.workflows import AgentWorkflowRegistry, default_workflow_registry


SAFE_FAILED_MESSAGE = "Agent runtime could not execute this workflow safely in the current phase."
SAFE_BLOCKED_MESSAGE = "Agent runtime blocked this request before workflow execution."


class AgentRuntime:
    def __init__(self, registry: AgentWorkflowRegistry | None = None) -> None:
        self.registry = registry or default_workflow_registry()
        self.safety_policy = safety.AgentSafetyPolicy()

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
            input_decision = self.safety_policy.evaluate_input(request.user_message, requested_workflow)
            service.record_safety_check(
                db,
                request_id=request_id,
                workflow_name=workflow_name,
                safety_level=safety.to_agent_safety_level(input_decision),
                passed=input_decision.allowed and not input_decision.blocked,
                safety_flags=list(input_decision.matched_rules),
                blocked_reason=input_decision.reason_code if input_decision.blocked else None,
                input_risk_summary=input_decision.reason_code,
            )
            if input_decision.blocked:
                blocked_message = self.safety_policy.build_safe_blocked_message(input_decision)
                service.fail_trace(
                    db,
                    trace.id,
                    error_type="safety_blocked",
                    error_message=input_decision.reason_code,
                    final_output_summary=blocked_message,
                    status=AgentTraceStatus.BLOCKED,
                )
                db.commit()
                return AgentRunResult(
                    trace_id=trace.id,
                    status="blocked",
                    workflow_type=requested_workflow,
                    message=blocked_message,
                    blocked=True,
                    safety_level=input_decision.safety_level,
                    generated_content=None,
                )

            handler = self.registry.get(workflow_name)
            workflow_result = handler.run(
                AgentWorkflowContext(
                    db=db,
                    trace_id=trace.id,
                    request=request,
                    safety_level=input_decision.safety_level,
                )
            )
            output_decision = self.safety_policy.evaluate_output(workflow_result.generated_content or workflow_result.message, requested_workflow)
            service.record_safety_check(
                db,
                request_id=request_id,
                workflow_name=workflow_name,
                safety_level=safety.to_agent_safety_level(output_decision),
                passed=output_decision.allowed and not output_decision.blocked,
                safety_flags=list(output_decision.matched_rules),
                blocked_reason=output_decision.reason_code if output_decision.blocked else None,
                input_risk_summary=f"output:{output_decision.reason_code}",
            )
            message = workflow_result.message
            generated_content = workflow_result.generated_content
            blocked = False
            safety_level = input_decision.safety_level
            if output_decision.blocked:
                message = output_decision.safe_message
                generated_content = output_decision.safe_message
                blocked = True
                safety_level = output_decision.safety_level
            elif input_decision.safety_level != "safe":
                safety_level = input_decision.safety_level
            service.complete_trace(db, trace.id, final_output_summary=safety.excerpt_text(message))
            db.commit()
            return AgentRunResult(
                trace_id=trace.id,
                status="completed",
                workflow_type=workflow_name.value,
                message=message,
                blocked=blocked,
                safety_level=safety_level,
                tool_calls_count=workflow_result.tool_calls_count,
                generated_content=generated_content,
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
