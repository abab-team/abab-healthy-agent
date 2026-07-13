"""Deterministic mock provider for tests and local development."""

from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage
from app.llm.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        if request.metadata.get("prompt_name") == "health_query_planner_v1":
            return LLMResponse(
                content=(
                    '{"intent":"query_blood_pressure","member_scope":"self",'
                    '"metric_type":"blood_pressure","time_range":"last_7_days",'
                    '"aggregation":"summary","confidence":0.92,'
                    '"needs_clarification":false,"clarification_question":null}'
                ),
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
        if request.metadata.get("prompt_name") == "health_answer_composer_v1":
            return LLMResponse(
                content=(
                    "Based on system records, I organized the available information. "
                    "This does not replace a doctor's judgment."
                ),
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
        if request.metadata.get("conversation_intent") == "casual_chat":
            return LLMResponse(
                content="你好，很高兴和你聊天。想聊聊今天的近况，或看看已经记录的健康信息，都可以直接告诉我。",
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
        if request.metadata.get("conversation_intent") == "health_knowledge":
            return LLMResponse(
                content="睡不好常和作息变化、压力、睡前刺激、环境或身体不适有关。可以先观察这些日常因素；如果困扰持续或伴随明显不适，建议咨询医生。",
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
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
