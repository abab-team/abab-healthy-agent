from __future__ import annotations

from dataclasses import dataclass, replace

from app.agent.chat.schemas import HealthQueryPlan
from app.agent.schemas import AgentRunRequest, AgentWorkflowContext
from app.modules.family import service as family_service
from app.modules.family.exceptions import (
    FamilyMemberNotFoundError,
    MemberReferenceAmbiguousError,
    MemberReferenceNotFoundError,
)


@dataclass(frozen=True)
class FamilyTargetResolution:
    request: AgentRunRequest | None
    plan: HealthQueryPlan
    display_name: str | None = None
    safe_message: str | None = None


def resolve_family_target(context: AgentWorkflowContext, plan: HealthQueryPlan) -> FamilyTargetResolution:
    """Resolve a deterministic family reference before ToolExecutor checks access."""
    if plan.member_scope != "family":
        return FamilyTargetResolution(request=context.request, plan=plan, display_name="我")
    if context.request.family_id is None or not plan.member_label:
        return FamilyTargetResolution(
            request=None,
            plan=plan,
            safe_message="要查询家人的记录，请先在当前家庭中选择成员后再试。",
        )
    try:
        resolved = family_service.resolve_member_reference(
            context.db,
            current_user_id=context.request.actor_user_id,
            current_family_id=context.request.family_id,
            member_reference=plan.member_label,
        )
    except (FamilyMemberNotFoundError, MemberReferenceNotFoundError, MemberReferenceAmbiguousError):
        return FamilyTargetResolution(
            request=None,
            plan=plan,
            safe_message="没有在当前家庭中确认到对应成员，请换一个更明确的称呼后再试。",
        )

    if resolved.target_user_id is None:
        return FamilyTargetResolution(
            request=None,
            plan=plan,
            safe_message="没有在当前家庭中确认到对应成员，请换一个更明确的称呼后再试。",
        )
    display_name = resolved.display_name or resolved.relationship_label or plan.member_label
    return FamilyTargetResolution(
        request=replace(context.request, target_user_id=resolved.target_user_id),
        plan=replace(plan, member_label=display_name, member_scope="family"),
        display_name=display_name,
    )
