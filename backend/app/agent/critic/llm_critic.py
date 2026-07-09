from __future__ import annotations

import json
from typing import Any

from app.agent.critic.rule_critic import RuleAnswerCritic, SAFE_REWRITE
from app.agent.critic.schemas import CriticReviewRequest, CriticReviewResult
from app.agent.prompts import PromptRegistry, get_prompt_registry
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client


class LLMAnswerCritic:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        prompt_registry: PromptRegistry | None = None,
        llm_client: LLMClient | Any | None = None,
        rule_critic: RuleAnswerCritic | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_registry = prompt_registry or get_prompt_registry()
        self.llm_client = llm_client
        self.rule_critic = rule_critic or RuleAnswerCritic()

    def review(self, request: CriticReviewRequest) -> CriticReviewResult:
        if not self.settings.LLM_CRITIC_ENABLED or not self.settings.LLM_ENABLED:
            return CriticReviewResult(passed=True, summary="llm_critic_disabled", critic_source="llm_disabled")
        try:
            prompt = self.prompt_registry.get_prompt("critic", version="v1")
            rendered = prompt.render(
                {
                    "user_question_excerpt": _safe_excerpt(request.user_question_excerpt, 300),
                    "safe_tool_result_summary": _safe_excerpt(request.safe_tool_result_summary, 1200),
                    "draft_answer": _safe_excerpt(request.draft_answer, 1200),
                    "policy_excerpt": (
                        "Reject diagnosis, prescription, dosage, medication-change advice, normal/abnormal risk "
                        "judgments, permission leaks, and claims not grounded in tool summaries."
                    ),
                }
            )
            client = self.llm_client or get_llm_client(self.settings)
            response = client.generate_text(
                system_prompt="Return JSON only for a safety critic. Do not call tools or infer facts.",
                user_prompt=rendered,
                temperature=0,
                max_tokens=min(self.settings.LLM_MAX_TOKENS, 500),
                metadata={
                    "workflow_type": request.workflow_type,
                    "prompt_name": "critic_v1",
                    "prompt_version": prompt.version,
                },
            )
            data = json.loads((response.content or "{}").strip())
            result = CriticReviewResult(
                passed=bool(data.get("passed")),
                risk_flags=_safe_list(data.get("risk_flags")),
                grounding_flags=_safe_list(data.get("grounding_flags")),
                rewrite_required=bool(data.get("rewrite_required")),
                safe_rewrite=_safe_excerpt(data.get("safe_rewrite"), 1000) or None,
                summary=_safe_excerpt(data.get("summary"), 300) or "llm_critic_reviewed",
                critic_source="llm",
            )
            if result.passed:
                return result
            rewrite = result.safe_rewrite or SAFE_REWRITE
            rule_result = self.rule_critic.review(
                CriticReviewRequest(
                    workflow_type=request.workflow_type,
                    user_question_excerpt=request.user_question_excerpt,
                    draft_answer=rewrite,
                    safe_tool_result_summary=request.safe_tool_result_summary,
                    tool_result_summaries=request.tool_result_summaries,
                    plan_intent=request.plan_intent,
                    time_range_label=request.time_range_label,
                )
            )
            if rule_result.passed:
                return CriticReviewResult(
                    passed=False,
                    risk_flags=result.risk_flags,
                    grounding_flags=result.grounding_flags,
                    rewrite_required=True,
                    safe_rewrite=rewrite,
                    summary=result.summary,
                    critic_source="llm",
                )
            return CriticReviewResult(
                passed=False,
                risk_flags=result.risk_flags + rule_result.risk_flags,
                grounding_flags=result.grounding_flags + rule_result.grounding_flags,
                rewrite_required=True,
                safe_rewrite=SAFE_REWRITE,
                summary="llm_rewrite_failed_rule_check",
                critic_source="llm",
            )
        except Exception:
            return CriticReviewResult(
                passed=False,
                risk_flags=["llm_critic_error"],
                grounding_flags=[],
                rewrite_required=True,
                safe_rewrite=SAFE_REWRITE,
                summary="llm_critic_failed_safely",
                critic_source="llm",
            )


def _safe_excerpt(value: Any, max_length: int) -> str:
    text = str(value or "").strip()
    return text[:max_length]


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value[:20]:
        text = _safe_excerpt(item, 80)
        if text:
            result.append(text)
    return result
