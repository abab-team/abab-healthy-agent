from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agent.memory import service as memory_service
from app.agent import service as agent_service
from app.agent.runtime import AgentRuntime
from app.agent.schemas import AgentRunRequest
from app.api.deps import get_current_user_id_for_demo, get_db
from app.api.errors import raise_bad_request, raise_not_found
from app.modules.agent.api_schemas import (
    ALLOWED_WORKFLOW_TYPES,
    CHAT_WORKFLOW,
    AgentMemoryItemResponse,
    AgentMessageResponse,
    AgentRunCreateRequest,
    AgentRunResponse,
    AgentSessionResponse,
    AgentSafetyCheckResponse,
    AgentToolCallResponse,
    AgentTraceResponse,
    agent_memory_item_response,
    agent_message_response,
    agent_run_response,
    agent_session_response,
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
    session_id = _prepare_session_id(db, payload, current_user_id)
    result = AgentRuntime().run(
        db,
        AgentRunRequest(
            actor_user_id=current_user_id,
            target_user_id=payload.target_user_id,
            family_id=payload.family_id,
            workflow_type=payload.workflow_type,
            user_message=payload.user_message,
            source=payload.source,
            request_id=payload.request_id,
            session_id=session_id,
            confirmation=payload.confirmation,
            workflow_payload=workflow_payload,
        ),
    )
    return agent_run_response(result)


@router.get("/memory", response_model=list[AgentMemoryItemResponse])
def list_agent_memory_items(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[AgentMemoryItemResponse]:
    return [agent_memory_item_response(item) for item in memory_service.list_memory_items(db, user_id=current_user_id)]


@router.delete("/memory/{memory_id}")
def delete_agent_memory_item(
    memory_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    deleted = memory_service.delete_memory_item(db, user_id=current_user_id, memory_id=memory_id)
    if not deleted:
        raise_not_found()
    db.commit()
    return {"deleted": True}


@router.get("/sessions", response_model=list[AgentSessionResponse])
def list_agent_sessions(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[AgentSessionResponse]:
    return [agent_session_response(session) for session in memory_service.list_sessions(db, user_id=current_user_id)]


@router.get("/sessions/{session_id}/messages", response_model=list[AgentMessageResponse])
def list_agent_session_messages(
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[AgentMessageResponse]:
    session = memory_service.get_session_for_user(db, session_id=session_id, user_id=current_user_id)
    if session is None:
        raise_not_found()
    messages = memory_service.list_session_messages(db, session_id=session.id, user_id=current_user_id)
    return [agent_message_response(message) for message in messages]


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
    response_workflow_type = agent_trace_response(trace).workflow_type
    return [agent_safety_check_response(check, workflow_type=response_workflow_type) for check in checks]


def _get_owned_trace_or_404(db: Session, trace_id: UUID, current_user_id: UUID):
    trace = agent_service.get_trace(db, trace_id)
    if trace is None or trace.current_user_id != current_user_id:
        raise_not_found()
    return trace


def _prepare_session_id(db: Session, payload: AgentRunCreateRequest, current_user_id: UUID) -> str | None:
    if payload.workflow_type != CHAT_WORKFLOW:
        return None
    if payload.session_id is not None:
        session = memory_service.get_session_for_user(db, session_id=payload.session_id, user_id=current_user_id)
        if session is None:
            raise_not_found()
        return str(session.id)
    session = memory_service.get_or_create_session(
        db,
        user_id=current_user_id,
        family_id=payload.family_id,
        title=payload.user_message,
    )
    return str(session.id)
