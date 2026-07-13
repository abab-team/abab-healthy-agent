from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.agent.chat.router import ConversationIntent, ConversationRoute, SuggestedAction
from app.agent.conversation import tasks
from app.agent.models import AgentConversationTask
from app.agent.schemas import AgentWorkflowContext


_CANCEL_MARKERS = ("取消", "算了", "不记录了", "结束这个")
_ORGANIZE_MARKERS = ("整理", "生成草稿", "预览")
_CONFIRM_MARKERS = ("确认", "提交", "保存")
_START_NOW_MARKERS = ("刚才", "现在", "今天", "刚开始")
_DURATION_PATTERN = re.compile(r"(?:持续|大概|约)?\s*(\d{1,3})\s*(分钟|分|小时|天)")
_TEMPERATURE_PATTERN = re.compile(r"(?:体温|温度)\s*(\d{2}(?:\.\d+)?)\s*(?:度|℃|c)?", re.IGNORECASE)


@dataclass(frozen=True)
class ConversationTaskDecision:
    handled: bool
    answer: str | None = None
    suggested_action: str | None = None
    task_state: dict[str, Any] | None = None


class ConversationManager:
    """State-first continuation layer for controlled conversational tasks.

    It owns no health facts and never invokes health tools. It only maintains a
    short-lived draft navigation state before the existing confirmed workflows.
    """

    def handle_active_task(
        self,
        context: AgentWorkflowContext,
        route: ConversationRoute,
    ) -> ConversationTaskDecision:
        task = tasks.get_active_task(context.db, session_id=context.request.session_id)
        if task is None:
            paused = tasks.get_latest_paused_task(context.db, session_id=context.request.session_id)
            if paused is not None and _is_task_continuation(context.request.user_message, route):
                tasks.resume_task(context.db, paused)
                return self._continue_task(context, paused, (context.request.user_message or "").strip())
            return ConversationTaskDecision(handled=False)

        message = (context.request.user_message or "").strip()
        if _contains(message, _CANCEL_MARKERS):
            tasks.cancel_task(context.db, task)
            return ConversationTaskDecision(
                handled=True,
                answer="好的，已取消这次草稿整理，不会写入任何健康记录。",
                task_state=tasks.safe_task_summary(task),
            )
        if not _is_task_continuation(message, route):
            tasks.pause_task(context.db, task)
            return ConversationTaskDecision(handled=False, task_state=tasks.safe_task_summary(task))
        return self._continue_task(context, task, message)

    def start_record_task(self, context: AgentWorkflowContext, route: ConversationRoute) -> ConversationTaskDecision:
        if route.intent != ConversationIntent.RECORD_TASK or route.suggested_action is None:
            return ConversationTaskDecision(handled=False)
        if not context.request.session_id:
            return ConversationTaskDecision(handled=False)

        task_type, payload, missing_fields = _initial_task_data(route.suggested_action, context.request.user_message)
        task = tasks.create_task(
            context.db,
            session_id=context.request.session_id,
            task_type=task_type,
            task_payload=payload,
            missing_fields=missing_fields,
        )
        if task is None:
            return ConversationTaskDecision(handled=False)
        if missing_fields:
            answer = "我先记下了这条待整理信息。它大约是什么时候开始的？"
        else:
            answer = "我已记下待整理的信息。你可以说“整理一下”，我会生成待确认草稿；在你确认前不会写入正式健康记录。"
        return ConversationTaskDecision(
            handled=True,
            answer=answer,
            suggested_action=route.suggested_action.value if not missing_fields else None,
            task_state=tasks.safe_task_summary(task),
        )

    def _continue_task(
        self,
        context: AgentWorkflowContext,
        task: AgentConversationTask,
        message: str,
    ) -> ConversationTaskDecision:
        payload = dict(task.task_payload or {})
        missing = list(task.missing_fields or [])
        if task.task_type == "symptom_draft":
            if "start_time" in missing and _is_start_time(message):
                payload["start_time"] = _excerpt(message)
                missing.remove("start_time")
            duration = _duration(message)
            if "duration" in missing and duration:
                payload["duration"] = duration
                missing.remove("duration")

        if _contains(message, _ORGANIZE_MARKERS):
            if missing:
                tasks.update_task(context.db, task, task_payload=payload, missing_fields=missing)
                return ConversationTaskDecision(
                    handled=True,
                    answer=_missing_prompt(missing),
                    task_state=tasks.safe_task_summary(task),
                )
            tasks.update_task(context.db, task, task_payload=payload, missing_fields=[], status="ready_for_preview")
            return ConversationTaskDecision(
                handled=True,
                answer="我已把这次信息整理为待确认草稿。请先打开草稿预览核对内容；预览不会写入，明确确认后才会进入现有受控流程。",
                suggested_action=_suggested_action_for_task(task.task_type),
                task_state=tasks.safe_task_summary(task),
            )

        if _contains(message, _CONFIRM_MARKERS):
            if missing:
                tasks.update_task(context.db, task, task_payload=payload, missing_fields=missing)
                return ConversationTaskDecision(handled=True, answer=_missing_prompt(missing), task_state=tasks.safe_task_summary(task))
            tasks.update_task(context.db, task, task_payload=payload, missing_fields=[], status="awaiting_confirmation")
            return ConversationTaskDecision(
                handled=True,
                answer="这份草稿已准备好。请在草稿预览页核对后再明确确认；这里不会直接写入正式健康记录。",
                suggested_action=_suggested_action_for_task(task.task_type),
                task_state=tasks.safe_task_summary(task),
            )

        tasks.update_task(context.db, task, task_payload=payload, missing_fields=missing)
        return ConversationTaskDecision(
            handled=True,
            answer=_missing_prompt(missing) if missing else "信息已经收集好。你可以说“整理一下”生成待确认草稿，或说“取消”。",
            task_state=tasks.safe_task_summary(task),
        )


def _initial_task_data(action: SuggestedAction, message: str) -> tuple[str, dict[str, Any], list[str]]:
    if action == SuggestedAction.SYMPTOM_DRAFT:
        return "symptom_draft", {"entity": "symptom", "label": _symptom_label(message)}, ["start_time", "duration"]
    if action == SuggestedAction.HEALTH_EVENT_DRAFT:
        temperature = _TEMPERATURE_PATTERN.search(message)
        payload: dict[str, Any] = {"entity": "health_event"}
        if temperature:
            payload.update({"metric_type": "temperature", "value": temperature.group(1), "unit": "C"})
        return "health_event_draft", payload, []
    return "health_alert", {"entity": "alert"}, []


def _symptom_label(message: str) -> str:
    for label in ("头晕", "头痛", "咳嗽", "发热", "睡不好", "不舒服"):
        if label in message:
            return label
    return "用户提到的不适"


def _is_start_time(message: str) -> bool:
    return _contains(message, _START_NOW_MARKERS) or bool(re.search(r"\d{1,3}\s*(分钟|分|小时|天)前", message))


def _duration(message: str) -> str | None:
    match = _DURATION_PATTERN.search(message)
    return f"{match.group(1)}{match.group(2)}" if match else None


def _missing_prompt(fields: list[str]) -> str:
    if "start_time" in fields:
        return "我还需要知道大约从什么时候开始。比如“刚才开始的”。"
    if "duration" in fields:
        return "我还需要知道大约持续了多久。比如“持续10分钟”。"
    return "还需要补充一些信息后才能整理草稿。"


def _suggested_action_for_task(task_type: str) -> str:
    return {
        "symptom_draft": SuggestedAction.SYMPTOM_DRAFT.value,
        "health_event_draft": SuggestedAction.HEALTH_EVENT_DRAFT.value,
        "health_alert": SuggestedAction.HEALTH_ALERT.value,
    }.get(task_type, SuggestedAction.SYMPTOM_DRAFT.value)


def _contains(message: str, markers: tuple[str, ...]) -> bool:
    return any(marker in message for marker in markers)


def _is_task_continuation(message: str, route: ConversationRoute) -> bool:
    """Only explicit task supplements may claim an active draft.

    Fresh queries, health questions, and casual turns pause a draft first so
    the existing Router can serve them. The draft remains resumable.
    """
    text = (message or "").strip()
    if route.intent == ConversationIntent.RECORD_TASK and not _starts_new_record_task(text):
        return True
    if _contains(text, (*_ORGANIZE_MARKERS, *_CONFIRM_MARKERS, *_CANCEL_MARKERS, *_START_NOW_MARKERS)):
        return True
    return _duration(text) is not None


def _starts_new_record_task(message: str) -> bool:
    """Keep a fresh record request from being merged into an older draft."""
    return any(marker in message for marker in ("\u8bb0\u5f55", "\u5e2e\u6211\u8bb0", "\u65b0\u5efa"))


def _excerpt(message: str) -> str:
    return message[:120]
