from __future__ import annotations

from app.agent.enums import AgentSafetyLevel
from app.agent.schemas import AgentSafetyDecision, AgentSafetyResult, MAX_AGENT_USER_MESSAGE_LENGTH


GENERAL_SAFE_MESSAGE = (
    "I can help organize system records and prepare safe notes, but I cannot provide a medical diagnosis, "
    "prescription, medication dosage, or medication change advice."
)
CAUTION_MESSAGE = (
    "I cannot replace a clinician's diagnosis. I can help record symptoms, organize system records, "
    "or prepare questions to discuss with a doctor."
)
MEDICATION_BLOCKED_MESSAGE = (
    "I cannot recommend medication names, dosages, or whether to start, stop, or change medication. "
    "Please consult a qualified clinician, and I can help you record questions to bring to them."
)
EMERGENCY_MESSAGE = (
    "This may be urgent. I cannot diagnose or provide treatment instructions. If the situation feels urgent, "
    "please contact local emergency services or a clinician as soon as possible."
)
SELF_HARM_MESSAGE = (
    "I am sorry you are feeling this way. Please seek immediate help from local emergency services, a crisis "
    "support line, or a trusted person nearby. I cannot provide harmful details, but you deserve support now."
)
OUTPUT_BLOCKED_MESSAGE = (
    "I replaced an unsafe response with a safer message. I can help organize system records, but I cannot "
    "provide diagnosis, prescription, dosage, medication change, or certainty claims."
)

DIAGNOSIS_TERMS = (
    "diagnose",
    "diagnosis",
    "what disease",
    "what illness",
    "do i have",
    "is this hypertension",
    "am i hypertensive",
    "诊断",
    "什么病",
    "是不是高血压",
    "我得了",
)
PRESCRIPTION_TERMS = (
    "prescribe",
    "prescription",
    "what medicine",
    "which medicine",
    "take medicine",
    "what drug",
    "开药",
    "处方",
    "吃什么药",
    "用什么药",
)
DOSAGE_TERMS = (
    "dosage",
    "dose",
    "how many pills",
    "how much medicine",
    "mg should i take",
    "剂量",
    "吃多少",
    "用量",
    "多少毫克",
)
MEDICATION_CHANGE_TERMS = (
    "stop medication",
    "stop taking",
    "change medication",
    "switch medication",
    "quit medicine",
    "停药",
    "换药",
    "减药",
    "加量",
)
EMERGENCY_TERMS = (
    "chest pain",
    "shortness of breath",
    "difficulty breathing",
    "fainted",
    "stroke",
    "severe headache",
    "heavy bleeding",
    "blood pressure 180/120",
    "bp 180/120",
    "胸痛",
    "呼吸困难",
    "昏厥",
    "中风",
    "大出血",
)
SELF_HARM_TERMS = (
    "kill myself",
    "end my life",
    "suicide",
    "self harm",
    "hurt myself",
    "do not want to live",
    "自杀",
    "不想活",
    "伤害自己",
)
RECORD_TERMS = (
    "record",
    "log",
    "note",
    "symptom",
    "slept badly",
    "headache today",
    "记录",
    "症状",
    "头疼",
    "睡不好",
)
SUMMARY_TERMS = (
    "summarize",
    "organize",
    "system records",
    "recent records",
    "checkup report",
    "doctor visit summary",
    "总结",
    "整理",
    "系统记录",
    "就医摘要",
)
UNSAFE_OUTPUT_TERMS = (
    "you definitely have",
    "you certainly have",
    "no need to see a doctor",
    "do not need to see a doctor",
    "it is definitely fine",
    "nothing is wrong",
    "take 2 pills",
    "take two pills",
    "stop your medication",
    "increase your dose",
    "decrease your dose",
    "i diagnose",
    "the diagnosis is",
    "你肯定得了",
    "不用看医生",
    "诊断是",
    "吃两片",
    "停药",
)


class AgentSafetyPolicy:
    def evaluate_input(self, user_message: str, workflow_type: str | None = None) -> AgentSafetyDecision:
        text = _normalize_text(user_message)
        if not text:
            return _decision(
                allowed=False,
                blocked=True,
                safety_level="blocked",
                category="unknown",
                reason_code="empty_input",
                safe_message="Please enter a message before running the Agent.",
                disallowed_actions=("run_workflow",),
                matched_rules=("empty_input",),
            )
        if len(text) > MAX_AGENT_USER_MESSAGE_LENGTH:
            return _decision(
                allowed=False,
                blocked=True,
                safety_level="blocked",
                category="unknown",
                reason_code="input_too_long",
                safe_message="The message is too long for this Agent phase. Please shorten it and try again.",
                disallowed_actions=("run_workflow",),
                matched_rules=("input_length_limit",),
            )

        lowered = text.lower()
        if matched := _match_terms(lowered, SELF_HARM_TERMS):
            return _decision(
                allowed=False,
                blocked=True,
                safety_level="emergency",
                category="self_harm",
                reason_code="self_harm_risk",
                safe_message=SELF_HARM_MESSAGE,
                requires_human_review=True,
                requires_medical_attention=True,
                disallowed_actions=("run_workflow", "provide_harmful_details"),
                allowed_actions=("supportive_safety_message",),
                matched_rules=matched,
            )
        if matched := _match_terms(lowered, EMERGENCY_TERMS):
            return _decision(
                allowed=False,
                blocked=True,
                safety_level="emergency",
                category="emergency_symptom",
                reason_code="emergency_symptom",
                safe_message=EMERGENCY_MESSAGE,
                requires_human_review=True,
                requires_medical_attention=True,
                disallowed_actions=("diagnose", "provide_treatment_plan", "run_workflow"),
                allowed_actions=("suggest_local_emergency_or_clinician_contact",),
                matched_rules=matched,
            )
        if matched := _match_terms(lowered, MEDICATION_CHANGE_TERMS):
            return _medication_block("medication_change_request", "medication_change_request", matched)
        if matched := _match_terms(lowered, DOSAGE_TERMS):
            return _medication_block("dosage_request", "dosage_request", matched)
        if matched := _match_terms(lowered, PRESCRIPTION_TERMS):
            return _medication_block("prescription_request", "prescription_request", matched)
        if matched := _match_terms(lowered, DIAGNOSIS_TERMS):
            return _decision(
                allowed=True,
                blocked=False,
                safety_level="caution",
                category="diagnosis_request",
                reason_code="diagnosis_boundary",
                safe_message=CAUTION_MESSAGE,
                requires_human_review=True,
                disallowed_actions=("diagnose", "state_condition_certainty"),
                allowed_actions=("record_symptoms", "organize_system_records", "prepare_doctor_questions"),
                matched_rules=matched,
            )
        if matched := _match_terms(lowered, SUMMARY_TERMS):
            return _decision(
                allowed=True,
                blocked=False,
                safety_level="safe",
                category="health_summary",
                reason_code="system_record_summary_allowed",
                safe_message="I can help summarize system records without making a diagnosis.",
                allowed_actions=("summarize_system_records", "prepare_doctor_questions"),
                matched_rules=matched,
            )
        if matched := _match_terms(lowered, RECORD_TERMS):
            return _decision(
                allowed=True,
                blocked=False,
                safety_level="safe",
                category="record_keeping",
                reason_code="record_keeping_allowed",
                safe_message="I can help create a record draft without making a diagnosis.",
                allowed_actions=("record_symptoms", "create_draft"),
                matched_rules=matched,
            )
        return _decision(
            allowed=True,
            blocked=False,
            safety_level="safe",
            category="general",
            reason_code="safe_input",
            safe_message=GENERAL_SAFE_MESSAGE,
            allowed_actions=("run_workflow",),
        )

    def evaluate_output(self, generated_content: str, workflow_type: str | None = None) -> AgentSafetyDecision:
        text = _normalize_text(generated_content)
        if not text:
            return _decision(
                allowed=True,
                blocked=False,
                safety_level="safe",
                category="general",
                reason_code="empty_output",
                safe_message=GENERAL_SAFE_MESSAGE,
                allowed_actions=("return_empty_output",),
            )
        lowered = text.lower()
        unsafe_terms = UNSAFE_OUTPUT_TERMS + DIAGNOSIS_TERMS + PRESCRIPTION_TERMS + DOSAGE_TERMS + MEDICATION_CHANGE_TERMS
        if matched := _match_terms(lowered, unsafe_terms):
            return _decision(
                allowed=False,
                blocked=True,
                safety_level="blocked",
                category="medical_question",
                reason_code="unsafe_medical_output",
                safe_message=OUTPUT_BLOCKED_MESSAGE,
                requires_human_review=True,
                disallowed_actions=("return_original_output",),
                allowed_actions=("return_safe_replacement",),
                matched_rules=matched,
            )
        return _decision(
            allowed=True,
            blocked=False,
            safety_level="safe",
            category="general",
            reason_code="safe_output",
            safe_message=GENERAL_SAFE_MESSAGE,
            allowed_actions=("return_output",),
        )

    def build_safe_blocked_message(self, decision: AgentSafetyDecision) -> str:
        return decision.safe_message

    def build_caution_message(self, decision: AgentSafetyDecision) -> str:
        return decision.safe_message


def check_user_message(user_message: str) -> AgentSafetyResult:
    decision = AgentSafetyPolicy().evaluate_input(user_message)
    return AgentSafetyResult(
        passed=decision.allowed and not decision.blocked,
        safety_level=to_agent_safety_level(decision),
        flags=list(decision.matched_rules),
        blocked_reason=decision.reason_code if decision.blocked else None,
        input_risk_summary=decision.reason_code,
    )


def to_agent_safety_level(decision: AgentSafetyDecision) -> AgentSafetyLevel:
    if decision.safety_level == "safe":
        return AgentSafetyLevel.SAFE
    if decision.safety_level == "caution":
        return AgentSafetyLevel.CAUTION
    if decision.safety_level in {"high_risk", "emergency"}:
        return AgentSafetyLevel.HIGH_RISK
    return AgentSafetyLevel.BLOCKED


def excerpt_text(value: str | None, *, max_length: int = 200) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:max_length]


def _normalize_text(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ""


def _match_terms(text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(term for term in terms if term in text)


def _medication_block(category: str, reason_code: str, matched_rules: tuple[str, ...]) -> AgentSafetyDecision:
    return _decision(
        allowed=False,
        blocked=True,
        safety_level="high_risk",
        category=category,
        reason_code=reason_code,
        safe_message=MEDICATION_BLOCKED_MESSAGE,
        requires_human_review=True,
        disallowed_actions=("provide_medication_name", "provide_dosage", "advise_medication_change", "run_workflow"),
        allowed_actions=("record_question_for_doctor",),
        matched_rules=matched_rules,
    )


def _decision(
    *,
    allowed: bool,
    blocked: bool,
    safety_level: str,
    category: str,
    reason_code: str,
    safe_message: str,
    requires_human_review: bool = False,
    requires_medical_attention: bool = False,
    disallowed_actions: tuple[str, ...] = (),
    allowed_actions: tuple[str, ...] = (),
    matched_rules: tuple[str, ...] = (),
) -> AgentSafetyDecision:
    return AgentSafetyDecision(
        allowed=allowed,
        blocked=blocked,
        safety_level=safety_level,
        category=category,
        reason_code=reason_code,
        safe_message=safe_message,
        requires_human_review=requires_human_review,
        requires_medical_attention=requires_medical_attention,
        disallowed_actions=disallowed_actions,
        allowed_actions=allowed_actions,
        matched_rules=matched_rules,
    )
