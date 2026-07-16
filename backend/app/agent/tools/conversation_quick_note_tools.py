from __future__ import annotations

from typing import Any

from uuid import UUID

from app.agent.conversation.quick_note_service import confirm_pending_task_by_id, create_pending_candidate
from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool


class ConversationQuickNoteDraftCreateTool(AgentTool):
    """Creates a pending, session-owned candidate only, never a health fact."""

    metadata = AgentToolMetadata(
        name="conversation.quick_note_draft.create",
        description="Create a user-confirmable quick-note candidate from a server-validated conversation candidate.",
        category="health_record",
        access_mode="draft",
        risk_level="low",
        required_permission_type="symptoms",
        required_permission_action="create",
        requires_confirmation=False,
        input_schema_name="QuickNoteCandidate",
        output_schema_name="PendingQuickNoteDraft",
        safety_notes=("Creates only a pending candidate; confirmation is required before a formal health record exists.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        candidate = payload.get("candidate")
        session_id = payload.get("session_id")
        if not isinstance(candidate, dict) or not session_id:
            raise ValueError("candidate and session_id are required")
        return {"candidate": candidate, "session_id": str(session_id)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return create_pending_candidate(payload["_db"], session_id=payload["session_id"], candidate=payload["candidate"])


class ConversationQuickNoteConfirmTool(AgentTool):
    """The only formal-write bridge for a confirmed conversation quick note."""

    metadata = AgentToolMetadata(
        name="conversation.quick_note.confirm",
        description="Confirm a session-owned quick-note candidate and save it through existing services.",
        category="system",
        access_mode="write",
        risk_level="medium",
        required_permission_type="metrics",
        required_permission_action="create",
        requires_confirmation=True,
        input_schema_name="QuickNoteConfirmInput",
        output_schema_name="QuickNoteConfirmOutput",
        safety_notes=("Requires an explicit user confirmation and never accepts a target user from the client.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"task_id": str(UUID(str(payload["task_id"]))), "session_id": str(UUID(str(payload["session_id"]))) }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return confirm_pending_task_by_id(
            payload["_db"],
            task_id=UUID(payload["task_id"]),
            session_id=UUID(payload["session_id"]),
            user_id=payload["_actor_user_id"],
            family_id=payload.get("_family_id"),
        )
