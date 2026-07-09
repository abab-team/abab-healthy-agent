from __future__ import annotations

from typing import Any

from app.agent.critic.llm_critic import LLMAnswerCritic
from app.agent.critic.rule_critic import RuleAnswerCritic, SAFE_REWRITE
from app.agent.critic.schemas import CriticReviewRequest, CriticReviewResult
from app.agent.safety import AgentSafetyPolicy
from app.core.config import Settings, get_settings


class AnswerCriticService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        rule_critic: RuleAnswerCritic | None = None,
        llm_critic: LLMAnswerCritic | Any | None = None,
        safety_policy: AgentSafetyPolicy | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.rule_critic = rule_critic or RuleAnswerCritic()
        self.llm_critic = llm_critic or LLMAnswerCritic(settings=self.settings, rule_critic=self.rule_critic)
        self.safety_policy = safety_policy or AgentSafetyPolicy()

    def review(self, request: CriticReviewRequest) -> CriticReviewResult:
        if not self.settings.RULE_CRITIC_ENABLED:
            return CriticReviewResult(passed=True, summary="rule_critic_disabled", critic_source="disabled")

        rule_result = self.rule_critic.review(request)
        result = rule_result
        if rule_result.passed and self.settings.LLM_CRITIC_ENABLED:
            result = self.llm_critic.review(request)
        elif not rule_result.passed and self.settings.LLM_CRITIC_ENABLED:
            llm_result = self.llm_critic.review(request)
            if llm_result.safe_rewrite:
                result = CriticReviewResult(
                    passed=False,
                    risk_flags=rule_result.risk_flags + llm_result.risk_flags,
                    grounding_flags=rule_result.grounding_flags + llm_result.grounding_flags,
                    rewrite_required=True,
                    safe_rewrite=llm_result.safe_rewrite,
                    summary="rule_and_llm_critic_failed",
                    critic_source="rule+llm",
                )

        if result.rewrite_required:
            rewrite = result.safe_rewrite or SAFE_REWRITE
            safety_decision = self.safety_policy.evaluate_output(rewrite, workflow_type=request.workflow_type)
            if safety_decision.blocked:
                rewrite = SAFE_REWRITE
            return CriticReviewResult(
                passed=False,
                risk_flags=result.risk_flags,
                grounding_flags=result.grounding_flags,
                rewrite_required=True,
                safe_rewrite=rewrite,
                summary=result.summary,
                critic_source=result.critic_source,
            )
        return result
