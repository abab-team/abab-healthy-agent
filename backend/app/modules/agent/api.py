from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agent import service as agent_service
from app.agent.runtime import AgentRuntime
from app.agent.schemas import AgentRunRequest
from app.api.deps import get_current_user_id_for_demo, get_db
from app.api.errors import raise_bad_request, raise_not_found
from app.modules.agent.api_schemas import (
    ALLOWED_WORKFLOW_TYPES,
    AgentRunCreateRequest,
    AgentRunResponse,
    AgentSafetyCheckResponse,
    AgentToolCallResponse,
    AgentTraceResponse,
    agent_run_response,
    agent_safety_check_response,
    agent_tool_call_response,
    agent_trace_response,
    workflow_payload_for_runtime,
)


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
def create_agent_run(
    payload: AgentRunCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> AgentRunResponse:
    if payload.workflow_type not in ALLOWED_WORKFLOW_TYPES:
        raise_bad_request("Requested agent workflow is not available in this phase.")
    if payload.target_user_id != current_user_id and payload.family_id is None:
        raise_bad_request("family_id is required for family member agent runs.")
    try:
        workflow_payload = workflow_payload_for_runtime(payload)
    except ValueError as exc:
        raise_bad_request(str(exc))
    result = AgentRuntime().run(
        db,
        AgentRunRequest(
            actor_user_id=current_user_id,
            target_user_id=payload.target_user_id,
            family_id=payload.family_id,
            workflow_type=payload.workflow_type,
            user_message=payload.user_message,
            source=payload.source,
            confirmation=payload.confirmation,
            workflow_payload=workflow_payload,
        ),
    )
    return agent_run_response(result)


@router.get("/runs/{trace_id}", response_model=AgentTraceResponse)
def get_agent_run(
    trace_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> AgentTraceResponse:
    trace = _get_owned_trace_or_404(db, trace_id, current_user_id)
    return agent_trace_response(trace)


@router.get("/runs/{trace_id}/tool-calls", response_model=list[AgentToolCallResponse])
def list_agent_run_tool_calls(
    trace_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[AgentToolCallResponse]:
    _get_owned_trace_or_404(db, trace_id, current_user_id)
    return [agent_tool_call_response(tool_call) for tool_call in agent_service.list_tool_calls(db, trace_id=trace_id)]


@router.get("/runs/{trace_id}/safety-checks", response_model=list[AgentSafetyCheckResponse])
def list_agent_run_safety_checks(
    trace_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[AgentSafetyCheckResponse]:
    trace = _get_owned_trace_or_404(db, trace_id, current_user_id)
    checks = agent_service.list_safety_checks(db, request_id=trace.request_id, workflow_name=trace.workflow_name)
    return [agent_safety_check_response(check) for check in checks]


def _get_owned_trace_or_404(db: Session, trace_id: UUID, current_user_id: UUID):
    trace = agent_service.get_trace(db, trace_id)
    if trace is None or trace.current_user_id != current_user_id:
        raise_not_found()
    return trace
