from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.prompts import PromptRegistry, get_prompt_registry
from app.agent.safety import AgentSafetyPolicy
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client


DEFAULT_SAFETY_BOUNDARY = (
    "以下内容仅基于系统内已有记录整理，不替代医生判断。"
)


@dataclass(frozen=True)
class AnswerComposerResult:
    answer: str
    llm_used: bool
    fallback_used: bool
    fallback_reason: str | None = None


class LLMAnswerComposer:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        prompt_registry: PromptRegistry | None = None,
        llm_client: LLMClient | Any | None = None,
        safety_policy: AgentSafetyPolicy | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_registry = prompt_registry or get_prompt_registry()
        self.llm_client = llm_client
        self.safety_policy = safety_policy or AgentSafetyPolicy()

    def compose(
        self,
        *,
        safe_tool_result_summary: str,
        coverage_note: str,
        user_question_excerpt: str = "",
        fallback_answer: str,
    ) -> AnswerComposerResult:
        if not self.settings.LLM_ANSWER_COMPOSER_ENABLED:
            return AnswerComposerResult(fallback_answer, llm_used=False, fallback_used=True, fallback_reason="composer_disabled")
        try:
            prompt = self.prompt_registry.get_prompt("health_answer_composer", version="v1")
            user_prompt = prompt.render(
                {
                    "safe_tool_result_summary": _safe_excerpt(safe_tool_result_summary, 1200),
                    "coverage_note": _safe_excerpt(coverage_note, 500),
                    "safety_boundary": DEFAULT_SAFETY_BOUNDARY,
                    "user_question_excerpt": _safe_excerpt(user_question_excerpt, 300),
                }
            )
            client = self.llm_client or get_llm_client(self.settings)
            response = client.generate_text(
                system_prompt=(
                    "只重写安全的系统内记录摘要，不要补充医疗建议。"
                    "所有面向用户的内容必须使用简体中文，并说明内容基于系统内记录且不替代医生判断。"
                ),
                user_prompt=user_prompt,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
                metadata={
                    "workflow_type": "chat_workflow",
                    "prompt_name": "health_answer_composer_v1",
                    "prompt_version": prompt.version,
                },
            )
            content = (response.content or "").strip()
            if not content:
                return AnswerComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="empty_output")
            if not _contains_cjk(content):
                return AnswerComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="output_not_chinese")
            decision = self.safety_policy.evaluate_output(content, workflow_type="chat_workflow")
            if decision.blocked:
                return AnswerComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason=decision.reason_code)
            return AnswerComposerResult(content, llm_used=True, fallback_used=False)
        except Exception:
            return AnswerComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="composer_failed")


def _safe_excerpt(value: Any, max_length: int) -> str:
    text = str(value or "").strip()
    return text[:max_length]


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)
