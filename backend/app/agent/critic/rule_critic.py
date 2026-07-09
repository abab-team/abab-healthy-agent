from __future__ import annotations

import re

from app.agent.critic.schemas import CriticReviewRequest, CriticReviewResult, ToolResultSummary


SAFE_REWRITE = (
    "Based on system records only, I can summarize available records, but I cannot provide medical conclusions, "
    "medication instructions, or certainty claims. Some information may be "
    "unavailable because of permissions or because the system has no matching records. This does not replace a "
    "doctor's judgment. If you feel unwell or the situation is urgent, please contact a clinician or local "
    "emergency service."
)

FORBIDDEN_MEDICAL_TERMS = (
    "diagnosis",
    "diagnose",
    "confirmed disease",
    "prescription",
    "prescribe",
    "dosage",
    "dose",
    "stop medication",
    "change medication",
    "normal",
    "abnormal",
    "high risk",
    "low risk",
    "no need to see a doctor",
    "definitely fine",
    "nothing is wrong",
    "you are fine",
    "确诊",
    "诊断",
    "处方",
    "剂量",
    "停药",
    "正常",
    "异常",
    "高风险",
    "低风险",
    "不用就医",
    "一定没事",
)

FORBIDDEN_DEBUG_TERMS = (
    "tool_name",
    "input_data",
    "raw_text",
    "symptom_text",
    "raw_extracted_text",
    "file_path",
    "traceback",
    "sql",
    "token",
    "password",
    "api_key",
    "private_key",
)

SYSTEM_RECORD_MARKERS = (
    "system records",
    "system record",
    "系统内记录",
    "绯荤粺鍐",
)

NO_RECORD_MARKERS = (
    "no matching records",
    "no records",
    "system has no",
    "系统内暂无",
    "没有相关记录",
    "绯荤粺鍐呮殏",
)

NO_RECORD_MISLEADING_TERMS = (
    "nothing is wrong",
    "no problem",
    "you are fine",
    "definitely fine",
    "没有问题",
    "不用担心",
    "一定没事",
)

PERMISSION_SAFE_MARKERS = (
    "unavailable because of permissions",
    "permission",
    "权限",
    "鏉冮檺",
)


class RuleAnswerCritic:
    def review(self, request: CriticReviewRequest) -> CriticReviewResult:
        text = request.draft_answer or ""
        lowered = text.lower()
        risk_flags: list[str] = []
        grounding_flags: list[str] = []

        for term in FORBIDDEN_MEDICAL_TERMS:
            if term.lower() in lowered or term in text:
                risk_flags.append(f"forbidden_medical_term:{_flag_name(term)}")

        for term in FORBIDDEN_DEBUG_TERMS:
            if term.lower() in lowered:
                risk_flags.append(f"debug_leak:{_flag_name(term)}")

        if not _contains_any(lowered, text, SYSTEM_RECORD_MARKERS):
            grounding_flags.append("missing_system_record_boundary")

        if _contains_any(lowered, text, NO_RECORD_MARKERS) and _contains_any(lowered, text, NO_RECORD_MISLEADING_TERMS):
            grounding_flags.append("no_record_misleading_claim")

        if _has_blocked_tool(request.tool_result_summaries) and not _contains_any(lowered, text, PERMISSION_SAFE_MARKERS):
            grounding_flags.append("permission_block_not_explained_safely")

        count_flag = _check_count_consistency(text, request.tool_result_summaries)
        if count_flag:
            grounding_flags.append(count_flag)

        passed = not risk_flags and not grounding_flags
        return CriticReviewResult(
            passed=passed,
            risk_flags=_unique(risk_flags),
            grounding_flags=_unique(grounding_flags),
            rewrite_required=not passed,
            safe_rewrite=None if passed else SAFE_REWRITE,
            summary="passed" if passed else "failed:" + ",".join(_unique(risk_flags + grounding_flags))[:300],
            critic_source="rule",
        )


def _contains_any(lowered: str, original: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in lowered or term in original for term in terms)


def _has_blocked_tool(summaries: tuple[ToolResultSummary, ...]) -> bool:
    return any(summary.blocked or summary.status not in {"completed", "success"} for summary in summaries)


def _check_count_consistency(text: str, summaries: tuple[ToolResultSummary, ...]) -> str | None:
    expected_counts = [summary.count for summary in summaries if summary.count is not None and summary.count >= 0]
    if len(expected_counts) != 1:
        return None
    expected = expected_counts[0]
    lowered = text.lower()
    match = re.search(r"\b(\d+)\s+(?:records?|items?|entries?)\b", lowered)
    if match and int(match.group(1)) != expected:
        return "tool_count_answer_mismatch"
    return None


def _flag_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")[:80]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
