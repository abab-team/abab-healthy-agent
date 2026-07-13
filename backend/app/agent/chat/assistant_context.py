from __future__ import annotations

from app.agent.schemas import AgentWorkflowContext
from app.modules.family import service as family_service
from app.modules.identity import service as identity_service


def build_assistant_context(context: AgentWorkflowContext) -> tuple[str, ...]:
    """Return a low-sensitivity conversational context, never identifiers.

    This is constructed by the controlled workflow, not by an LLM. Health data
    and permission outcomes remain owned by ToolExecutor and are injected only
    after a tool call has been checked.
    """

    lines: list[str] = []
    user = identity_service.get_user(context.db, context.request.actor_user_id)
    if user is not None and user.nickname:
        lines.append(f"当前用户称呼: {user.nickname[:64]}")
    if context.request.family_id is not None:
        members = family_service.list_family_members(context.db, context.request.family_id)
        labels = [
            (member.display_name or member.relationship_label or "家庭成员")[:64]
            for member in members[:12]
        ]
        if labels:
            lines.append("当前家庭成员: " + "、".join(labels))
        lines.append("家人健康信息只能使用已经通过现有权限检查后提供的事实。")
    return tuple(lines)
