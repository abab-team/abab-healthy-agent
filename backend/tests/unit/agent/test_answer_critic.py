from __future__ import annotations

import unittest

from app.agent.critic import AnswerCriticService, CriticReviewRequest, ToolResultSummary
from app.agent.critic.rule_critic import RuleAnswerCritic
from app.core.config import Settings


class AnswerCriticTestCase(unittest.TestCase):
    def test_safe_answer_passes(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="How many sleep records do I have?",
                draft_answer=(
                    "Based on system records only, there are 2 records in the selected range. "
                    "This does not replace a doctor's judgment."
                ),
                safe_tool_result_summary="count=2; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.metric.summary", "completed", count=2),),
            )
        )

        self.assertTrue(result.passed)
        self.assertFalse(result.rewrite_required)

    def test_chinese_system_record_boundary_passes(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="\u67e5\u8be2\u8840\u538b",
                draft_answer=(
                    "\u7cfb\u7edf\u8bb0\u5f55\u663e\u793a\uff0c\u8fc7\u53bb7\u5929\u5185\u5171\u67092\u6761\u8840\u538b\u8bb0\u5f55\u3002"
                    "\u6b64\u6458\u8981\u4ec5\u57fa\u4e8e\u7cfb\u7edf\u5185\u5df2\u6709\u8bb0\u5f55\uff0c\u4e0d\u66ff\u4ee3\u533b\u751f\u7684\u4e13\u4e1a\u5224\u65ad\u3002"
                ),
                safe_tool_result_summary="count=2; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.blood_pressure.summary", "completed", count=2),),
            )
        )

        self.assertTrue(result.passed)

    def test_composer_style_chinese_boundary_passes(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="\u67e5\u8be2\u8840\u538b",
                draft_answer=(
                    "\u6700\u8fd17\u5929\u5185\uff0c\u7cfb\u7edf\u5171\u8bb0\u5f55\u4e863\u6b21\u8840\u538b\u6570\u636e\u3002\n"
                    "\u4ee5\u4e0a\u5185\u5bb9\u4ec5\u57fa\u4e8e\u7cfb\u7edf\u5185\u5df2\u6709\u8bb0\u5f55\u6574\u7406\uff0c\u4e0d\u66ff\u4ee3\u533b\u751f\u5224\u65ad\u3002"
                ),
                safe_tool_result_summary="count=3; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.blood_pressure.summary", "completed", count=3),),
            )
        )

        self.assertTrue(result.passed)

    def test_no_record_misleading_claim_fails(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="Do I have records?",
                draft_answer="Based on system records only, no records were found, so nothing is wrong.",
                safe_tool_result_summary="count=0; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_record.symptoms.query", "completed", count=0),),
            )
        )

        self.assertFalse(result.passed)
        self.assertTrue(result.rewrite_required)
        self.assertIn("no_record_misleading_claim", result.grounding_flags)

    def test_medication_stop_advice_fails_and_rewrites(self) -> None:
        result = AnswerCriticService(settings=Settings()).review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="What should I do?",
                draft_answer="Based on system records only, you should stop medication.",
                safe_tool_result_summary="count=1; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.metric.summary", "completed", count=1),),
            )
        )

        self.assertFalse(result.passed)
        self.assertTrue(result.rewrite_required)
        self.assertIsNotNone(result.safe_rewrite)
        self.assertNotIn("stop medication", (result.safe_rewrite or "").lower())
        self.assertIn("\u7cfb\u7edf\u5185\u5df2\u6709\u8bb0\u5f55", result.safe_rewrite or "")

    def test_llm_critic_cannot_replace_a_rule_grounded_answer(self) -> None:
        class RejectingLlmCritic:
            def review(self, _request: CriticReviewRequest):
                from app.agent.critic.schemas import CriticReviewResult

                return CriticReviewResult(
                    passed=False,
                    rewrite_required=True,
                    safe_rewrite="Generic fallback",
                    critic_source="llm",
                )

        settings = Settings(LLM_CRITIC_ENABLED=True)
        result = AnswerCriticService(settings=settings, llm_critic=RejectingLlmCritic()).review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="How many blood pressure records do I have?",
                draft_answer=(
                    "Based on system records only, there are 2 records in the selected range. "
                    "This does not replace a doctor's judgment."
                ),
                safe_tool_result_summary="count=2; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.blood_pressure.summary", "completed", count=2),),
            )
        )

        self.assertTrue(result.passed)
        self.assertFalse(result.rewrite_required)

    def test_normal_abnormal_medical_judgment_fails(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="How is my blood pressure?",
                draft_answer="Based on system records only, your blood pressure is normal.",
                safe_tool_result_summary="count=1; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.blood_pressure.summary", "completed", count=1),),
            )
        )

        self.assertFalse(result.passed)
        self.assertTrue(any(flag.startswith("forbidden_medical_term") for flag in result.risk_flags))

    def test_missing_system_record_boundary_fails(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="How many records?",
                draft_answer="There are 3 records in the selected range.",
                safe_tool_result_summary="count=3; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.metric.summary", "completed", count=3),),
            )
        )

        self.assertFalse(result.passed)
        self.assertIn("missing_system_record_boundary", result.grounding_flags)

    def test_tool_count_mismatch_fails(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="How many records?",
                draft_answer="Based on system records only, there are 1 records in the selected range.",
                safe_tool_result_summary="count=2; system_records_only",
                tool_result_summaries=(ToolResultSummary("health_data.metric.summary", "completed", count=2),),
            )
        )

        self.assertFalse(result.passed)
        self.assertIn("tool_count_answer_mismatch", result.grounding_flags)

    def test_debug_leak_fails(self) -> None:
        result = RuleAnswerCritic().review(
            CriticReviewRequest(
                workflow_type="chat_workflow",
                user_question_excerpt="What files?",
                draft_answer="Based on system records only, tool_name=documents.query file_path=storage://private/report.pdf",
                safe_tool_result_summary="count=1; system_records_only",
                tool_result_summaries=(ToolResultSummary("documents.query", "completed", count=1),),
            )
        )

        self.assertFalse(result.passed)
        self.assertTrue(any(flag.startswith("debug_leak") for flag in result.risk_flags))


if __name__ == "__main__":
    unittest.main()
