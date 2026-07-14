"""Display-only bridge for the existing session-message API."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.memory import service as memory_service


def mirror_turn_for_display(
    db: Session,
    *,
    session_id: UUID | str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Store short safe summaries for the legacy read-only message endpoint.

    These summaries are deliberately not read by Conversation Runtime V2. Native
    LangGraph checkpoints remain its sole source of conversational continuity.
    """

    memory_service.append_message(
        db,
        session_id=session_id,
        role="user",
        content=sanitize_checkpoint_message(user_message, max_chars=500),
    )
    memory_service.append_message(
        db,
        session_id=session_id,
        role="assistant",
        content=sanitize_checkpoint_message(assistant_message, max_chars=500),
    )
