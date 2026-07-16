"""Deterministic mock provider for tests and local development."""

from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage
from app.llm.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        if request.metadata.get("agent_mode") == "business_tool_loop":
            content = _conversation_v3_response(request)
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                is_mock=True,
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                finish_reason="mock",
            )
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


def _conversation_v3_response(request: LLMRequest) -> str:
    """A deterministic local stand-in for the strict V3 Agent JSON contract.

    This is test/development-only provider behavior. Production intent
    understanding comes from the configured LLM, while the runtime itself
    remains free of keyword-to-tool routing.
    """
    import json

    user_messages = [item.content for item in request.messages if item.role == "user"]
    system_messages = [item.content for item in request.messages if item.role == "system"]
    latest = user_messages[-1] if user_messages else ""
    tool_facts = next((item for item in reversed(user_messages) if item.startswith("已授权工具事实")), "")
    if tool_facts and latest.startswith("已授权工具事实"):
        try:
            payload = json.loads(tool_facts[tool_facts.find("{") :])
        except (ValueError, IndexError):
            payload = {}
        facts = payload.get("facts") if isinstance(payload, dict) else {}
        subject = payload.get("subject_label", "你") if isinstance(payload, dict) else "你"
        bp = facts.get("blood_pressure") if isinstance(facts, dict) else None
        if isinstance(bp, dict) and bp.get("latest"):
            average = f"，已记录数值的平均值约为 {bp['average']}" if bp.get("average") else ""
            return json.dumps({"type": "final", "content": f"我刚刚查到{subject}最近一次血压记录是 {bp['latest']}{average}。单次记录只能作为一次测量参考；如果你愿意，我可以继续帮你看更长时间范围的变化。"}, ensure_ascii=False)
        items = "、".join(key for key, value in facts.items() if isinstance(value, dict) and value.get("record_count", 0))
        if isinstance(payload, dict) and payload.get("unavailable_sections") and not facts:
            return json.dumps({"type": "final", "content": "这部分记录暂不可用，我不会据此编造内容。你可以稍后再试，或换一个已授权的项目查看。"}, ensure_ascii=False)
        return json.dumps({"type": "final", "content": f"我已经整理了{subject}这段时间可查看的记录。{('目前包含' + items + '。') if items else '系统内暂时没有可展示的相关记录。'} 你还可以继续问其中某一项。"}, ensure_ascii=False)
    prior_payload = {}
    if tool_facts:
        try:
            prior_payload = json.loads(tool_facts[tool_facts.find("{") :])
        except (ValueError, IndexError):
            prior_payload = {}
    lower = latest.lower()
    if isinstance(prior_payload, dict) and any(word in latest for word in ("这个数值", "健康吗", "怎么样")):
        facts = prior_payload.get("facts") if isinstance(prior_payload.get("facts"), dict) else {}
        bp = facts.get("blood_pressure") if isinstance(facts, dict) else None
        if isinstance(bp, dict) and bp.get("latest"):
            return json.dumps({"type": "final", "content": f"刚才查到的记录是 {bp['latest']}。从常见成人静息血压参考范围来看，这个单次读数可以作为日常记录参考；单次测量不能代表长期情况，继续看一段时间的变化会更有帮助。"}, ensure_ascii=False)
    if "天气" in latest:
        return json.dumps({"type": "final", "content": "我目前不能查询实时天气。不过我可以陪你聊聊，或在权限允许的范围内整理健康记录。"}, ensure_ascii=False)
    if any(word in latest for word in ("记录", "修改", "改成", "写入", "体温", "头晕")):
        return json.dumps({"type": "final", "content": "我现在的对话入口只支持聊天和已授权记录查询，草稿写入暂时没有开启，因此不会保存这条信息。"}, ensure_ascii=False)
    if any(word in latest for word in ("感冒", "睡不好", "失眠")):
        return json.dumps({"type": "final", "content": "这类情况常和作息变化、压力、环境或短期身体不适有关。可以先留意休息、补水和症状变化；如果不适持续、加重或让你担心，建议咨询医生。"}, ensure_ascii=False)
    inherited_subject = prior_payload.get("subject_label") if isinstance(prior_payload, dict) else None
    subject = "爸爸" if any(word in latest for word in ("爸爸", "父亲", "我爸")) else ("妈妈" if any(word in latest for word in ("妈妈", "母亲", "我妈")) else (inherited_subject or "self"))
    period = "30d" if any(word in latest for word in ("30天", "一个月", "上个月")) else "7d"
    if isinstance(prior_payload, dict) and period != "7d" and prior_payload.get("capability") == "metric_detail" and prior_payload.get("metric"):
        return json.dumps({"type": "tool_call", "name": "metric_detail", "arguments": {"subject_reference": subject, "metric": prior_payload["metric"], "period": period}}, ensure_ascii=False)
    if any(word in latest for word in ("最近怎么样", "健康情况", "身体怎么样", "除了血压还有什么", "不只是血压")):
        return json.dumps({"type": "tool_call", "name": "health_overview", "arguments": {"subject_reference": subject, "period": period}}, ensure_ascii=False)
    metric_map = (("血压", "blood_pressure"), ("睡眠", "sleep"), ("体重", "weight"), ("步数", "steps"), ("心率", "heart_rate"), ("bmi", "bmi"))
    for label, metric in metric_map:
        if label in lower or label in latest:
            return json.dumps({"type": "tool_call", "name": "metric_detail", "arguments": {"subject_reference": subject, "metric": metric, "period": period}}, ensure_ascii=False)
    if any(word in latest for word in ("文档", "报告", "资料")):
        return json.dumps({"type": "tool_call", "name": "document_overview", "arguments": {"subject_reference": subject, "period": period}}, ensure_ascii=False)
    if any(word in latest for word in ("提醒", "待办")):
        return json.dumps({"type": "tool_call", "name": "alert_overview", "arguments": {"subject_reference": subject, "period": period}}, ensure_ascii=False)
    if "我是谁" in latest:
        import re
        match = re.search(r"当前用户显示名：([^。\n]+)", "\n".join(system_messages))
        answer = f"你是{match.group(1) if match else '当前这段对话的用户'}，我会在这段对话里记住我们刚才聊过的内容。"
    elif "你是谁" in latest:
        answer = "我是你的家庭健康管家，可以陪你聊天，也能在权限允许的范围内整理自己和家人的健康记录。"
    elif "还记得" in latest:
        answer = "记得，我们还在同一段对话里。你可以接着刚才的话题继续问。"
    elif "你好" in latest or "心情不错" in latest:
        answer = "你好呀，今天过得怎么样？想聊聊天，或看看最近的健康记录，我都在。"
    else:
        answer = "我在。你可以直接和我聊天，也可以问我自己或家人已授权的健康记录。"
    return json.dumps({"type": "final", "content": answer}, ensure_ascii=False)
