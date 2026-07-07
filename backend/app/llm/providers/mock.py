"""Deterministic mock provider for tests and local development."""

from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage
from app.llm.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        if request.metadata.get("workflow_type") == "daily_health_brief":
            return LLMResponse(
                content=(
                    "根据系统内记录，已整理一份健康简报。\n"
                    "- 系统内记录已按健康档案、血压记录、症状记录、复查随访和提醒整理。\n"
                    "- 本简报不能替代医生诊断或治疗建议。\n"
                    "- 如有不适或紧急情况，请联系医生或当地急救服务。"
                ),
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
        return LLMResponse(
            content=(
                "Mock LLM response. This deterministic text is for local "
                "development only and has not executed a clinical workflow."
            ),
            provider=self.name,
            model=self.model,
            is_mock=True,
            usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            finish_reason="mock",
        )
