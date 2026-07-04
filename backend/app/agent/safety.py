from __future__ import annotations

from app.agent.enums import AgentSafetyLevel
from app.agent.schemas import AgentSafetyResult, MAX_AGENT_USER_MESSAGE_LENGTH


MEDICAL_CAUTION_KEYWORDS = (
    "diagnosis",
    "diagnose",
    "prescription",
    "dosage",
    "dose",
    "stop medication",
    "take medicine",
    "开药",
    "处方",
    "剂量",
    "诊断",
    "停药",
    "换药",
)


def check_user_message(user_message: str) -> AgentSafetyResult:
    text = user_message.strip() if isinstance(user_message, str) else ""
    if not text:
        return AgentSafetyResult(
            passed=False,
            safety_level=AgentSafetyLevel.BLOCKED,
            flags=["empty_input"],
            blocked_reason="empty_user_message",
            input_risk_summary="empty input",
        )
    if len(text) > MAX_AGENT_USER_MESSAGE_LENGTH:
        return AgentSafetyResult(
            passed=False,
            safety_level=AgentSafetyLevel.BLOCKED,
            flags=["input_too_long"],
            blocked_reason="user_message_too_long",
            input_risk_summary="input length exceeds limit",
        )
    lowered = text.lower()
    flags = [keyword for keyword in MEDICAL_CAUTION_KEYWORDS if keyword in lowered]
    if flags:
        return AgentSafetyResult(
            passed=True,
            safety_level=AgentSafetyLevel.CAUTION,
            flags=["medical_boundary_caution"],
            input_risk_summary="request mentions diagnosis, prescription, or dosage boundary",
        )
    return AgentSafetyResult(
        passed=True,
        safety_level=AgentSafetyLevel.SAFE,
        flags=[],
        input_risk_summary="no deterministic safety risk detected",
    )


def excerpt_text(value: str | None, *, max_length: int = 200) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:max_length]
