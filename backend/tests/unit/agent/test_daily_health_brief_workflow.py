from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07f_daily_health_brief.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.safety import AgentSafetyPolicy  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry, default_workflow_registry  # noqa: E402
from app.agent.workflows.daily_health_brief import (  # noqa: E402
    READONLY_HEALTH_BRIEF_TOOLS,
    DailyHealthBriefWorkflow,
    _daily_brief_system_prompt,
)
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.alerts import service as alert_service  # noqa: E402
from app.modules.alerts.enums import AlertLevel, AlertType  # noqa: E402
from app.modules.alerts.models import Alert  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.health_data.models import BloodPressureRecord  # noqa: E402
from app.modules.health_profile import service as health_profile_service  # noqa: E402
from app.modules.health_profile.models import HealthProfile  # noqa: E402
from app.modules.health_record import service as health_record_service  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.document_processing.models import MedicalEventDraft  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.identity.enums import Gender  # noqa: E402
from app.modules.medical_timeline import service as medical_timeline_service  # noqa: E402
from app.modules.medical_timeline.enums import MedicalEventType  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402
from app.modules.reports.models import DailyReport  # noqa: E402
from app.llm.errors import LLMProviderError, LLMTimeoutError  # noqa: E402
from app.llm.schemas import LLMResponse  # noqa: E402


READONLY_TOOL_NAMES = list(READONLY_HEALTH_BRIEF_TOOLS)
UNSAFE_OUTPUT_TERMS = (
    "正常",
    "异常",
    "高血压",
    "低血压",
    "prescription",
    "dosage",
    "stop medication",
    "take 2 pills",
    "不用看医生",
    "没有问题",
    "你很健康",
)


class FakeLLMClient:
    def __init__(self, content: str, *, raise_error: bool = False, exception: Exception | None = None, response=None) -> None:
        self.content = content
        self.raise_error = raise_error
        self.exception = exception
        self.response = response
        self.calls = 0
        self.last_user_prompt = ""

    def generate_text(self, *, system_prompt, user_prompt, temperature, max_tokens, metadata):
        del system_prompt, temperature, max_tokens
        self.calls += 1
        self.last_user_prompt = user_prompt
        if self.exception is not None:
            raise self.exception
        if self.raise_error:
            raise LLMProviderError("provider failed")
        if self.response is not None:
            return self.response
        return LLMResponse(
            content=self.content,
            provider="fake",
            model="fake-model",
            is_mock=True,
            finish_reason="fake",
        )


class DailyHealthBriefWorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase07f.actor.{suffix}@example.com",
            phone=f"p07f_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase07f.target.{suffix}@example.com",
            phone=f"p07f_target_{suffix}",
            nickname="Target",
            gender=Gender.FEMALE,
            birth_date=date(1988, 1, 1),
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 07F Family",
            owner_display_name="Actor",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            relationship_label="member",
            display_name="Target",
        )
        permissions_service.create_default_permissions_for_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            share_all=True,
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_daily_health_brief_workflow_is_registered(self) -> None:
        handler = default_workflow_registry().get(AgentWorkflowName.DAILY_HEALTH_BRIEF)

        self.assertIsInstance(handler, DailyHealthBriefWorkflow)

    def test_daily_brief_system_prompt_uses_health_companion_voice(self) -> None:
        prompt = _daily_brief_system_prompt()

        self.assertIn("健康小伙伴", prompt)
        self.assertIn("温柔、细心、自然", prompt)

    def test_rule_brief_prioritizes_recent_recorded_metrics_over_bmi(self) -> None:
        health_profile_service.create_or_update_profile(self.db, self.actor.id, {"height_cm": 182})
        health_data_service.add_metric(self.db, user_id=self.actor.id, metric_type="weight", value_numeric=65, unit="kg")

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        content = result.generated_content or ""

        self.assertIn("健康小结 🌱", content)
        self.assertIn("❤️ 身体指标", content)
        self.assertIn("最近 7 天记录了 1 次体重", content)
        self.assertNotIn("BMI 约为 19.6", content)
        self.assertIn("📌 小提醒", content)
        self.assertNotIn("记录连续", content)
        self.assertNotIn("资料归档", content)

    def test_runtime_executes_daily_health_brief_for_self_access(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None)

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertEqual(result.workflow_type, "daily_health_brief")
        self.assertEqual(result.tool_calls_count, len(READONLY_TOOL_NAMES))
        self.assertEqual([call.tool_name for call in calls], READONLY_TOOL_NAMES)
        self.assertTrue(all(call.status.value == "success" for call in calls))
        self.assertIn("基于系统内已有记录整理", result.generated_content or "")
        self.assertIn("健康小结 🌱", result.generated_content or "")
        self.assertIn("📌 小提醒", result.generated_content or "")

    def test_family_access_allowed_generates_brief(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id)

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), len(READONLY_TOOL_NAMES))
        self.assertTrue(all(call.permission_checked for call in calls))
        self.assertIn("记录了 1 次血压", result.generated_content or "")

    def test_family_access_denied_does_not_leak_target_data(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id, secret_text="private target symptom")
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_profile": False,
                "can_view_metrics": False,
                "can_view_symptoms": False,
                "can_view_medical_events": False,
                "can_view_documents": False,
                "can_view_alerts": False,
            },
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        content = result.generated_content or ""

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), len(READONLY_TOOL_NAMES))
        self.assertTrue(all(call.status.value == "blocked_by_permission" for call in calls))
        self.assertIn("部分信息因权限设置暂不可用", content)
        self.assertNotIn("private target symptom", content)

    def test_one_blocked_tool_still_returns_partial_safe_brief(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id)
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_profile": True,
                "can_view_metrics": True,
                "can_view_symptoms": False,
                "can_view_medical_events": True,
                "can_view_alerts": True,
            },
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), len(READONLY_TOOL_NAMES))
        self.assertIn("部分信息因权限设置暂不可用", result.generated_content or "")
        self.assertIn("基于系统内已有记录整理", result.generated_content or "")

    def test_no_records_uses_system_no_record_wording(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        content = result.generated_content or ""

        self.assertIn("目前系统内暂无足够的近期记录", content)
        self.assertNotIn("现实没有问题", content)
        self.assertNotIn("没有问题", content)

    def test_output_is_safe_and_output_safety_does_not_block(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        content = result.generated_content or ""

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertIn("不替代医生判断", content)
        self.assertIn("如有明显不适请及时就医", content)
        for term in UNSAFE_OUTPUT_TERMS:
            self.assertNotIn(term, content)

    def test_daily_health_brief_safety_exception_does_not_allow_medical_advice(self) -> None:
        content = "\n".join(
            [
                "根据系统内记录，已为你整理最近 7 天的健康简报：",
                "系统内暂无相关记录。",
                "本简报不能替代医生诊断或治疗建议。",
                "如有不适或紧急情况，请联系医生或当地急救服务。",
                "处方建议：停药并调整剂量。",
            ]
        )

        decision = AgentSafetyPolicy().evaluate_output(content, "daily_health_brief")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason_code, "unsafe_medical_output")

    def test_safety_exception_does_not_apply_to_other_workflows(self) -> None:
        content = "\n".join(
            [
                "根据系统内记录，已为你整理最近 7 天的健康简报：",
                "系统内暂无相关记录。",
                "本简报不能替代医生诊断或治疗建议。",
                "如有不适或紧急情况，请联系医生或当地急救服务。",
            ]
        )

        decision = AgentSafetyPolicy().evaluate_output(content, "chat_workflow")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason_code, "unsafe_medical_output")

    def test_default_workflow_does_not_call_llm_or_directly_access_repository_or_db(self) -> None:
        fake_llm = FakeLLMClient("should not be called")
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=False, DAILY_BRIEF_USE_LLM=False),
                llm_client=fake_llm,
            )
        )
        source = inspect.getsource(sys.modules[DailyHealthBriefWorkflow.__module__])

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 0)
        self.assertIn("llm_used=false", result.message)
        self.assertIn("fallback_reason=llm_disabled", result.message)
        self.assertNotIn("repository", source)
        self.assertNotIn("SessionLocal", source)
        self.assertNotIn("select(", source)
        self.assertNotIn(".query(", source)
        self.assertNotIn("from app.modules", source)

    def test_daily_brief_use_llm_false_does_not_call_llm(self) -> None:
        fake_llm = FakeLLMClient("should not be called")
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=False),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 0)
        self.assertIn("llm_used=false", result.message)
        self.assertIn("fallback_reason=daily_brief_use_llm_disabled", result.message)

    def test_llm_enabled_can_generate_safe_daily_brief(self) -> None:
        safe_content = "健康小结 🌱\n我帮你整理了最近 7 天的已记录信息。\n❤️ 身体指标\n最近一次血压记录为 118/76 mmHg。\n📌 小提醒\n继续积累已有记录。"
        fake_llm = FakeLLMClient(safe_content)
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertTrue((result.generated_content or "").startswith(safe_content))
        self.assertIn("llm_used=true", result.message)
        self.assertIn("fallback_used=false", result.message)
        self.assertNotIn("api_key", result.message.lower())
        self.assertNotIn("raw prompt", result.message.lower())

    def test_report_like_llm_output_falls_back_to_compact_companion_brief(self) -> None:
        fake_llm = FakeLLMClient("健康简报：\n- 血压记录 3 次\n- 睡眠记录 2 次\n- 体重记录 1 次")
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertIn("健康小结 🌱", result.generated_content or "")
        self.assertIn("📌 小提醒", result.generated_content or "")
        self.assertNotIn("\n-", result.generated_content or "")
        self.assertIn("fallback_reason=llm_output_not_compact", result.message)

    def test_llm_provider_error_falls_back_to_rule_brief(self) -> None:
        fake_llm = FakeLLMClient("", raise_error=True)
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertIn("基于系统内已有记录整理", result.generated_content or "")
        self.assertIn("fallback_used=true", result.message)
        self.assertIn("fallback_reason=llm_provider_error", result.message)

    def test_llm_timeout_falls_back_to_rule_brief(self) -> None:
        fake_llm = FakeLLMClient("", exception=LLMTimeoutError("request timed out"))
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertEqual(result.status, "completed")
        self.assertIn("fallback_used=true", result.message)
        self.assertIn("fallback_reason=llm_timeout", result.message)

    def test_empty_llm_output_falls_back_to_rule_brief(self) -> None:
        fake_llm = FakeLLMClient("   ")
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertEqual(result.status, "completed")
        self.assertIn("fallback_reason=empty_llm_output", result.message)

    def test_invalid_llm_response_schema_falls_back_to_rule_brief(self) -> None:
        fake_llm = FakeLLMClient("", response=object())
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertEqual(result.status, "completed")
        self.assertIn("fallback_reason=llm_response_invalid", result.message)

    def test_unsafe_llm_output_falls_back_to_rule_brief(self) -> None:
        fake_llm = FakeLLMClient("诊断结果：高风险，请停药并调整剂量。")
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(fake_llm.calls, 1)
        self.assertIn("基于系统内已有记录整理", result.generated_content or "")
        self.assertNotIn("诊断结果", result.generated_content or "")
        self.assertIn("fallback_reason=llm_output_safety_blocked", result.message)
        self.assertIn("safety_filtered=true", result.message)

    def test_unsafe_llm_fallback_records_safety_summary_without_raw_response(self) -> None:
        unsafe_output = "诊断结果：高风险，请停药并调整剂量。"
        fake_llm = FakeLLMClient(unsafe_output)
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))
        trace = agent_service.get_trace(self.db, result.trace_id)
        checks = agent_service.list_safety_checks(self.db, request_id=trace.request_id)
        joined = "\n".join(
            [
                str(check.safety_flags)
                + str(check.blocked_reason)
                + str(check.input_risk_summary)
                + str(check.original_answer_summary)
                + str(check.revised_answer_summary)
                for check in checks
            ]
        )

        self.assertIn("llm_output_safety_filtered", joined)
        self.assertIn("fallback_reason=llm_output_safety_blocked", joined)
        self.assertIn("llm_output_omitted", joined)
        self.assertNotIn(unsafe_output, joined)
        self.assertNotIn("api_key", joined.lower())
        self.assertNotIn("raw prompt", joined.lower())
        self.assertNotIn("raw response", joined.lower())

    def test_llm_prompt_uses_structured_summary_without_sensitive_raw_fields(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None, secret_text="very private raw symptom text")
        safe_content = "\n".join(
            [
                "根据系统内记录，已整理一份健康简报。",
                "- 系统内记录已完成摘要整理。",
                "- 本简报不能替代医生诊断或治疗建议。",
                "- 如有不适或紧急情况，请联系医生或当地急救服务。",
            ]
        )
        fake_llm = FakeLLMClient(safe_content)
        registry = AgentWorkflowRegistry()
        registry.register(
            DailyHealthBriefWorkflow(
                settings=Settings(LLM_ENABLED=True, DAILY_BRIEF_USE_LLM=True),
                llm_client=fake_llm,
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertNotIn("very private raw symptom text", fake_llm.last_user_prompt)
        self.assertNotIn("raw_text", fake_llm.last_user_prompt)
        self.assertNotIn("file_path", fake_llm.last_user_prompt)
        self.assertNotIn("raw_extracted_text", fake_llm.last_user_prompt)
        self.assertIn("可选健康重点", fake_llm.last_user_prompt)
        self.assertIn("严格保留以下栏目结构", fake_llm.last_user_prompt)
        self.assertIn("❤️ 身体指标", fake_llm.last_user_prompt)
        self.assertNotIn("资料与安排", fake_llm.last_user_prompt)
        self.assertNotIn("api_key", result.message.lower())

    def test_workflow_does_not_write_daily_reports_or_health_business_data(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None)
        counts_before = self._business_counts()

        AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(self._business_counts(), counts_before)

    def test_rag_enabled_keeps_internal_citations_out_of_user_content(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None)
        registry = AgentWorkflowRegistry()
        registry.register(DailyHealthBriefWorkflow(settings=Settings(RAG_ENABLED=True, RAG_TOP_K=3)))

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id))
        trace = agent_service.get_trace(self.db, result.trace_id)
        checks = agent_service.list_safety_checks(self.db, request_id=trace.request_id)
        joined_checks = "\n".join(str(check.safety_flags) + str(check.input_risk_summary) for check in checks)

        self.assertEqual(result.status, "completed")
        self.assertNotIn("System record citations", result.generated_content or "")
        self.assertNotIn("llm_used=", result.generated_content or "")
        self.assertNotIn("fallback_reason=", result.generated_content or "")
        self.assertIn("rag_daily_brief", joined_checks)
        self.assertIn("rag_used=true", joined_checks)
        self.assertNotIn("raw_text", result.generated_content or "")
        self.assertNotIn("file_path", result.generated_content or "")

    def test_blocked_input_does_not_execute_workflow_or_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, user_message="   "))
        trace = agent_service.get_trace(self.db, result.trace_id)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(trace.status, AgentTraceStatus.BLOCKED)
        self.assertEqual(calls, [])

    def test_trace_does_not_remain_running(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        trace = agent_service.get_trace(self.db, result.trace_id)

        self.assertNotEqual(trace.status, AgentTraceStatus.RUNNING)

    def _request(self, actor_user_id, target_user_id, *, family_id=None, user_message: str = "整理最近健康记录") -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            family_id=family_id,
            workflow_type="daily_health_brief",
            user_message=user_message,
            source="unit-test",
        )

    def _seed_health_records(self, user_id, created_by_user_id, *, family_id, secret_text: str = "headache after screen time") -> None:
        health_profile_service.create_or_update_profile(
            self.db,
            user_id,
            {"health_goal": "walk weekly", "allergy_summary": "pollen"},
        )
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=user_id,
            systolic=118,
            diastolic=76,
            pulse=70,
        )
        health_record_service.create_symptom_record(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            raw_text=secret_text,
            symptom_name="headache",
        )
        medical_timeline_service.create_medical_event(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="Follow-up record",
            follow_up_needed=True,
            follow_up_at=datetime.now(timezone.utc) + timedelta(days=3),
            doctor_advice="private doctor advice should not be returned",
        )
        alert_service.create_alert(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            alert_type=AlertType.DOCUMENT_REVIEW,
            level=AlertLevel.ATTENTION,
            title="Review document",
            message="Document review reminder.",
        )

    def _business_counts(self) -> dict[str, int]:
        return {
            "health_profiles": self.db.query(HealthProfile).count(),
            "blood_pressure_records": self.db.query(BloodPressureRecord).count(),
            "symptom_records": self.db.query(SymptomRecord).count(),
            "health_record_drafts": self.db.query(HealthRecordDraft).count(),
            "medical_events": self.db.query(MedicalEvent).count(),
            "medical_event_drafts": self.db.query(MedicalEventDraft).count(),
            "daily_reports": self.db.query(DailyReport).count(),
            "alerts": self.db.query(Alert).count(),
        }


if __name__ == "__main__":
    unittest.main()
