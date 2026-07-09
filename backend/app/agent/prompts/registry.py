from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agent.chat.schemas import HealthQueryIntent
from app.agent.prompts.schemas import PromptNotFoundError, PromptTemplate


PROMPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PROMPT_DIR / "templates"

HEALTH_QUERY_ALLOWED_INTENTS = tuple(intent.value for intent in HealthQueryIntent if intent != HealthQueryIntent.UNKNOWN)


class PromptRegistry:
    def __init__(self) -> None:
        self._prompts = _load_default_prompts()

    def get_prompt(self, name: str, version: str | None = None) -> PromptTemplate:
        candidates = [prompt for prompt in self._prompts.values() if prompt.name == name]
        if version is not None:
            candidates = [prompt for prompt in candidates if prompt.version == version]
        if not candidates:
            raise PromptNotFoundError(f"Prompt not registered: {name}:{version or 'latest'}")
        return sorted(candidates, key=lambda prompt: prompt.version)[-1]

    def list_prompts(self) -> list[PromptTemplate]:
        return sorted(self._prompts.values(), key=lambda prompt: prompt.prompt_id)

    def render_prompt(self, name: str, *, version: str | None = None, variables: dict[str, Any]) -> str:
        return self.get_prompt(name, version=version).render(variables)


def get_prompt_registry() -> PromptRegistry:
    return PromptRegistry()


def _load_default_prompts() -> dict[str, PromptTemplate]:
    prompts = [
        PromptTemplate(
            name="health_query_planner",
            version="v1",
            description="Plan a safe health-record query as constrained JSON.",
            input_schema={
                "user_message": {"type": "string", "required": True},
                "recent_session_context_summary": {"type": "string", "required": False},
                "safe_memory_summary": {"type": "string", "required": False},
                "allowed_intents": {"type": "array", "required": True},
                "allowed_metric_types": {"type": "array", "required": True},
                "allowed_member_scopes": {"type": "array", "required": True},
                "allowed_time_ranges": {"type": "array", "required": True},
            },
            output_schema={
                "intent": {"type": "string", "required": True},
                "member_scope": {"type": "string", "required": True},
                "metric_type": {"type": "string", "required": False},
                "time_range": {"type": "string", "required": True},
                "aggregation": {"type": "string", "required": False},
                "confidence": {"type": "number", "required": True},
                "needs_clarification": {"type": "boolean", "required": True},
                "clarification_question": {"type": "string", "required": False},
            },
            safety_notes=(
                "LLM must not choose tool_name or input_data.",
                "LLM must not decide user IDs, family IDs, or target user IDs.",
                "Planner output must be validated before any tool execution.",
            ),
            allowed_intents=HEALTH_QUERY_ALLOWED_INTENTS,
            created_at="2026-07-09",
            template=_read_template("health_query_planner_v1.md"),
        ),
        PromptTemplate(
            name="health_answer_composer",
            version="v1",
            description="Rewrite a safe tool-result summary without medical judgment.",
            input_schema={
                "safe_tool_result_summary": {"type": "string", "required": True},
                "coverage_note": {"type": "string", "required": True},
                "safety_boundary": {"type": "string", "required": True},
                "user_question_excerpt": {"type": "string", "required": False},
            },
            output_schema={"answer": {"type": "string", "required": True}},
            safety_notes=(
                "Do not diagnose, prescribe, dose, or recommend stopping medication.",
                "Do not say normal, abnormal, high risk, low risk, no need to see a doctor, or definitely fine.",
                "Mention that the answer is based on system records and does not replace a doctor.",
            ),
            allowed_intents=HEALTH_QUERY_ALLOWED_INTENTS,
            created_at="2026-07-09",
            template=_read_template("health_answer_composer_v1.md"),
        ),
        PromptTemplate(
            name="memory_extractor",
            version="v1",
            description="Extract user-editable non-medical preferences only.",
            input_schema={
                "user_message": {"type": "string", "required": True},
                "session_summary": {"type": "string", "required": False},
            },
            output_schema={
                "memory_type": {"type": "string", "required": False},
                "content": {"type": "string", "required": False},
                "should_store": {"type": "boolean", "required": True},
            },
            safety_notes=(
                "Do not store unconfirmed health facts.",
                "Do not store diagnosis, prescription, dosage, or medication changes.",
            ),
            allowed_intents=(),
            created_at="2026-07-09",
            template=_read_template("memory_extractor_v1.md"),
        ),
        PromptTemplate(
            name="critic",
            version="v1",
            description="Check generated answers for medical-safety and grounding risks.",
            input_schema={
                "answer": {"type": "string", "required": True},
                "safe_sources_summary": {"type": "string", "required": False},
            },
            output_schema={
                "passed": {"type": "boolean", "required": True},
                "reason_code": {"type": "string", "required": False},
                "safe_rewrite": {"type": "string", "required": False},
            },
            safety_notes=(
                "Reject diagnosis, prescription, dosage, medication-stop advice, and certainty claims.",
                "Reject answers not grounded in safe tool results.",
            ),
            allowed_intents=HEALTH_QUERY_ALLOWED_INTENTS,
            created_at="2026-07-09",
            template=_read_template("critic_v1.md"),
        ),
    ]
    return {prompt.prompt_id: prompt for prompt in prompts}


def _read_template(filename: str) -> str:
    return (TEMPLATE_DIR / filename).read_text(encoding="utf-8")
