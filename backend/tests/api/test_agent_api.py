from __future__ import annotations

import inspect
import unittest
import uuid

from backend.tests.api.helpers import (
    SessionLocal,
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)

from app.agent.enums import AgentMemorySource, AgentMemoryStatus, AgentMemoryType, AgentMemoryVisibility
from app.agent.models import AgentMemory
from app.modules.agent import api as agent_api
from app.modules.alerts.models import Alert
from app.modules.document_processing.models import MedicalEventDraft
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord
from app.modules.medical_timeline.models import MedicalEvent


UNSAFE_TERMS = (
    "diagnosis",
    "prescription",
    "dosage",
    "stop medication",
    "take 2 pills",
    "file_path",
    "raw_extracted_text",
    "password",
    "token",
    "api_key",
)


class AgentApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.actor = create_user("agent_actor", nickname="Agent Actor")
        self.target = create_user("agent_target", nickname="Agent Target")
        self.outsider = create_user("agent_outsider", nickname="Outsider")
        self.family = create_family(self.actor["id"])["family"]
        add_member(self.family["id"], self.actor["id"], self.target["id"], "member", "Target")
        create_permission_for_member(self.family["id"], self.actor["id"], share_all=True)
        create_permission_for_member(self.family["id"], self.target["id"], share_all=True)

    def test_missing_current_user_header_returns_unified_error(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            json=self._payload(target_user_id=self.actor["id"]),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "missing_current_user")
        self.assertIn("message", response.json()["detail"])
        self.assertIn("request_id", response.json()["detail"])
        self.assertIn("fields", response.json()["detail"])

    def test_invalid_workflow_type_is_rejected(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.actor["id"], workflow_type="chat_workflow"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "invalid_request")

    def test_daily_health_brief_can_run_through_api(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.actor["id"]),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(body["trace_id"])
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["workflow_type"], "daily_health_brief")
        self.assertIsInstance(body["generated_content"], str)
        self.assertGreater(len(body["generated_content"]), 100)
        self.assertGreater(body["tool_calls_count"], 0)
        for term in UNSAFE_TERMS:
            self.assertNotIn(term, response.text.lower())

    def test_chat_workflow_can_run_through_api(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="chat",
                user_message="最近一周我的血压记录怎么样？",
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["workflow_type"], "chat")
        self.assertEqual(body["status"], "completed")
        self.assertIsNotNone(body["session_id"])
        self.assertIn("根据系统内记录", body["generated_content"])
        self.assertEqual(body["tool_calls_count"], 1)
        for term in UNSAFE_TERMS:
            self.assertNotIn(term, response.text.lower())

    def test_chat_session_messages_can_be_listed_by_owner(self) -> None:
        run_response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="chat",
                user_message="最近 30 天血压记录怎么样？",
            ),
        )
        session_id = run_response.json()["session_id"]

        sessions_response = client.get("/api/v1/agent/sessions", headers=auth_headers(self.actor["id"]))
        messages_response = client.get(f"/api/v1/agent/sessions/{session_id}/messages", headers=auth_headers(self.actor["id"]))
        outsider_response = client.get(f"/api/v1/agent/sessions/{session_id}/messages", headers=auth_headers(self.outsider["id"]))

        self.assertEqual(sessions_response.status_code, 200)
        self.assertTrue(any(item["id"] == session_id for item in sessions_response.json()))
        self.assertEqual(messages_response.status_code, 200)
        self.assertGreaterEqual(len(messages_response.json()), 2)
        self.assertEqual(outsider_response.status_code, 404)
        for payload in (sessions_response.text, messages_response.text):
            lowered = payload.lower()
            self.assertNotIn("raw_text", lowered)
            self.assertNotIn("api_key", lowered)
            self.assertNotIn("password", lowered)

    def test_memory_list_and_delete_are_scoped_to_owner(self) -> None:
        with SessionLocal() as db:
            memory = AgentMemory(
                user_id=uuid.UUID(self.actor["id"]),
                memory_type=AgentMemoryType.USER_PREFERENCE,
                content="用户希望回答保持简洁。",
                source=AgentMemorySource.MANUAL,
                confidence_level=ConfidenceLevel.HIGH,
                visibility=AgentMemoryVisibility.PRIVATE,
                status=AgentMemoryStatus.ACTIVE,
            )
            db.add(memory)
            db.commit()
            memory_id = str(memory.id)

        list_response = client.get("/api/v1/agent/memory", headers=auth_headers(self.actor["id"]))
        outsider_delete = client.delete(f"/api/v1/agent/memory/{memory_id}", headers=auth_headers(self.outsider["id"]))
        delete_response = client.delete(f"/api/v1/agent/memory/{memory_id}", headers=auth_headers(self.actor["id"]))
        list_after_delete = client.get("/api/v1/agent/memory", headers=auth_headers(self.actor["id"]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(outsider_delete.status_code, 404)
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["deleted"])
        self.assertEqual(list_after_delete.json(), [])

    def test_chat_workflow_rejects_payload_and_generic_execution_fields(self) -> None:
        payload = self._payload(
            target_user_id=self.actor["id"],
            workflow_type="chat",
            user_message="最近一周我的睡眠记录怎么样？",
            workflow_payload={"tool_name": "health_data.metric.summary"},
        )

        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=payload,
        )

        self.assertIn(response.status_code, {400, 422})
        self.assertIn(response.json()["detail"]["code"], {"invalid_request", "validation_error"})

    def test_family_permission_allowed_runs_daily_health_brief(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.target["id"], family_id=self.family["id"]),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(response.json()["tool_calls_count"], 5)

    def test_family_permission_denied_does_not_leak_target_data(self) -> None:
        patch_response = client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.target['id']}/permissions",
            headers=auth_headers(self.actor["id"]),
            json={
                "share_all": False,
                "can_view_profile": False,
                "can_view_metrics": False,
                "can_view_symptoms": False,
                "can_view_medical_events": False,
                "can_view_alerts": False,
                "reason": "agent api denied test",
            },
        )
        self.assertEqual(patch_response.status_code, 200)

        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.target["id"], family_id=self.family["id"]),
        )

        self.assertEqual(response.status_code, 201)
        content = response.json()["generated_content"]
        self.assertGreater(len(content), 100)
        self.assertNotIn(self.target["email"], response.text)
        self.assertNotIn("target secret", response.text.lower())

    def test_symptom_draft_create_unconfirmed_does_not_write_draft(self) -> None:
        before = self._draft_counts()
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="symptom_draft_create",
                user_message="Please create a pending symptom draft.",
                confirmation=False,
                workflow_payload={"raw_text": "Record a mild symptom note."},
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["workflow_type"], "symptom_draft_create")
        self.assertIn("requires_confirmation", body["generated_content"])
        self.assertEqual(body["tool_calls_count"], 1)
        self.assertEqual(self._draft_counts(), before)

    def test_symptom_draft_create_confirmed_creates_pending_draft_only(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="symptom_draft_create",
                user_message="Please create a pending symptom draft.",
                confirmation=True,
                workflow_payload={"raw_text": "Record a mild symptom note."},
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["status"], "completed")
        self.assertIn("draft_id=", body["generated_content"])
        self.assertIn("formal_record_created=false", body["generated_content"])
        counts = self._draft_counts()
        self.assertEqual(counts["health_record_drafts"], 1)
        self.assertEqual(counts["symptom_records"], 0)
        for term in UNSAFE_TERMS + ("record a mild symptom note", "symptom_text"):
            self.assertNotIn(term, response.text.lower())

    def test_draft_trace_and_safety_responses_show_requested_workflow_type(self) -> None:
        run_response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="symptom_draft_create",
                user_message="Please create a pending symptom draft.",
                confirmation=True,
                workflow_payload={"raw_text": "Record a mild symptom note."},
            ),
        )
        trace_id = run_response.json()["trace_id"]

        trace_response = client.get(f"/api/v1/agent/runs/{trace_id}", headers=auth_headers(self.actor["id"]))
        safety_response = client.get(
            f"/api/v1/agent/runs/{trace_id}/safety-checks",
            headers=auth_headers(self.actor["id"]),
        )

        self.assertEqual(trace_response.status_code, 200)
        self.assertEqual(trace_response.json()["workflow_type"], "symptom_draft_create")
        self.assertEqual(safety_response.status_code, 200)
        self.assertTrue(safety_response.json())
        self.assertTrue(all(item["workflow_type"] == "symptom_draft_create" for item in safety_response.json()))

    def test_medical_event_draft_create_unconfirmed_does_not_write_draft(self) -> None:
        before = self._draft_counts()
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="medical_event_draft_create",
                user_message="Please create a pending event draft.",
                confirmation=False,
                workflow_payload={"draft_title": "Follow-up note", "summary": "User-provided follow-up note."},
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["workflow_type"], "medical_event_draft_create")
        self.assertIn("requires_confirmation", body["generated_content"])
        self.assertEqual(body["tool_calls_count"], 1)
        self.assertEqual(self._draft_counts(), before)

    def test_medical_event_draft_create_confirmed_creates_pending_draft_only(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="medical_event_draft_create",
                user_message="Please create a pending event draft.",
                confirmation=True,
                workflow_payload={"draft_title": "Follow-up note", "summary": "User-provided follow-up note."},
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["status"], "completed")
        self.assertIn("draft_id=", body["generated_content"])
        self.assertIn("formal_event_created=false", body["generated_content"])
        counts = self._draft_counts()
        self.assertEqual(counts["medical_event_drafts"], 1)
        self.assertEqual(counts["medical_events"], 0)
        for term in UNSAFE_TERMS + ("user-provided follow-up note",):
            self.assertNotIn(term, response.text.lower())

    def test_family_permission_denied_blocks_draft_workflow(self) -> None:
        patch_response = client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.target['id']}/permissions",
            headers=auth_headers(self.actor["id"]),
            json={
                "share_all": False,
                "can_create_symptom_records": False,
                "reason": "agent draft denied test",
            },
        )
        self.assertEqual(patch_response.status_code, 200)

        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.target["id"],
                family_id=self.family["id"],
                workflow_type="symptom_draft_create",
                user_message="Please create a pending symptom draft.",
                confirmation=True,
                workflow_payload={"raw_text": "target secret symptom"},
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("blocked", response.json()["generated_content"].lower())
        self.assertEqual(self._draft_counts()["health_record_drafts"], 0)
        self.assertNotIn("target secret symptom", response.text.lower())

    def test_family_permission_allowed_draft_workflow_can_execute(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.target["id"],
                family_id=self.family["id"],
                workflow_type="symptom_draft_create",
                user_message="Please create a pending symptom draft.",
                confirmation=True,
                workflow_payload={"raw_text": "Family member draft note."},
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["workflow_type"], "symptom_draft_create")
        self.assertEqual(self._draft_counts()["health_record_drafts"], 1)

    def test_get_run_tool_calls_and_safety_checks_for_owner(self) -> None:
        run_response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.actor["id"], user_message="raw_text secret token password api_key"),
        )
        trace_id = run_response.json()["trace_id"]

        trace_response = client.get(f"/api/v1/agent/runs/{trace_id}", headers=auth_headers(self.actor["id"]))
        tool_calls_response = client.get(
            f"/api/v1/agent/runs/{trace_id}/tool-calls",
            headers=auth_headers(self.actor["id"]),
        )
        safety_response = client.get(
            f"/api/v1/agent/runs/{trace_id}/safety-checks",
            headers=auth_headers(self.actor["id"]),
        )

        self.assertEqual(trace_response.status_code, 200)
        self.assertEqual(trace_response.json()["trace_id"], trace_id)
        self.assertEqual(tool_calls_response.status_code, 200)
        self.assertEqual(len(tool_calls_response.json()), 5)
        self.assertEqual(safety_response.status_code, 200)
        self.assertGreaterEqual(len(safety_response.json()), 2)
        for payload in (trace_response.text, tool_calls_response.text, safety_response.text):
            lowered = payload.lower()
            self.assertNotIn("raw_text secret", lowered)
            self.assertNotIn("api_key", lowered)
            self.assertNotIn("password", lowered)
            self.assertNotIn("file_path", lowered)
            self.assertNotIn("raw_extracted_text", lowered)

    def test_cannot_query_other_actor_trace(self) -> None:
        run_response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.actor["id"]),
        )
        trace_id = run_response.json()["trace_id"]

        trace_response = client.get(f"/api/v1/agent/runs/{trace_id}", headers=auth_headers(self.outsider["id"]))
        tool_calls_response = client.get(
            f"/api/v1/agent/runs/{trace_id}/tool-calls",
            headers=auth_headers(self.outsider["id"]),
        )
        safety_response = client.get(
            f"/api/v1/agent/runs/{trace_id}/safety-checks",
            headers=auth_headers(self.outsider["id"]),
        )

        self.assertEqual(trace_response.status_code, 404)
        self.assertEqual(tool_calls_response.status_code, 404)
        self.assertEqual(safety_response.status_code, 404)
        self.assertEqual(trace_response.json()["detail"]["code"], "resource_not_found")

    def test_family_run_requires_family_id(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.target["id"]),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "invalid_request")

    def test_agent_runs_reject_generic_tool_execution_fields(self) -> None:
        payload = self._payload(target_user_id=self.actor["id"])
        payload["tool_name"] = "alerts.create"
        payload["input_data"] = {"title": "not allowed"}

        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=payload,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "validation_error")

    def test_agent_runs_reject_direct_alert_create_workflow(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(target_user_id=self.actor["id"], workflow_type="alerts.create"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "invalid_request")

    def test_alert_create_unconfirmed_does_not_create_alert(self) -> None:
        before = self._draft_counts()
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="alert_create",
                user_message="Please create a regular follow-up reminder.",
                confirmation=False,
                workflow_payload=self._alert_payload(),
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["workflow_type"], "alert_create")
        self.assertIn("requires_confirmation", body["generated_content"])
        self.assertEqual(body["tool_calls_count"], 1)
        self.assertEqual(self._draft_counts(), before)

    def test_alert_create_confirmed_creates_alert(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="alert_create",
                user_message="Please create a regular follow-up reminder.",
                confirmation=True,
                workflow_payload=self._alert_payload(),
            ),
        )

        body = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["status"], "completed")
        self.assertIn("alert_id=", body["generated_content"])
        self.assertIn("external_dispatch=false", body["generated_content"])
        self.assertEqual(self._draft_counts()["alerts"], 1)
        for term in UNSAFE_TERMS + ("prepare materials before the planned visit",):
            self.assertNotIn(term, response.text.lower())

    def test_alert_create_requires_create_permission_not_view(self) -> None:
        patch_response = client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.target['id']}/permissions",
            headers=auth_headers(self.actor["id"]),
            json={
                "share_all": False,
                "can_view_alerts": True,
                "can_create_alerts": False,
                "reason": "agent alert denied test",
            },
        )
        self.assertEqual(patch_response.status_code, 200)

        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.target["id"],
                family_id=self.family["id"],
                workflow_type="alert_create",
                user_message="Please create a regular follow-up reminder.",
                confirmation=True,
                workflow_payload=self._alert_payload(),
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("blocked", response.json()["generated_content"].lower())
        self.assertEqual(self._draft_counts()["alerts"], 0)

    def test_alert_create_family_permission_allowed_can_execute(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.target["id"],
                family_id=self.family["id"],
                workflow_type="alert_create",
                user_message="Please create a regular follow-up reminder.",
                confirmation=True,
                workflow_payload=self._alert_payload(),
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["workflow_type"], "alert_create")
        self.assertEqual(self._draft_counts()["alerts"], 1)

    def test_alert_create_high_risk_request_does_not_create_alert(self) -> None:
        response = client.post(
            "/api/v1/agent/runs",
            headers=auth_headers(self.actor["id"]),
            json=self._payload(
                target_user_id=self.actor["id"],
                workflow_type="alert_create",
                user_message="I have chest pain and may hurt myself, create an emergency alarm.",
                confirmation=True,
                workflow_payload=self._alert_payload(),
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "blocked")
        self.assertEqual(response.json()["tool_calls_count"], 0)
        self.assertEqual(self._draft_counts()["alerts"], 0)
        self.assertNotIn("emergency alarm", response.text.lower())

    def test_alert_create_rejects_generic_execution_payload_fields(self) -> None:
        payload = self._payload(
            target_user_id=self.actor["id"],
            workflow_type="alert_create",
            confirmation=True,
            workflow_payload={**self._alert_payload(), "tool_name": "alerts.create", "input_data": {"title": "bad"}},
        )

        response = client.post("/api/v1/agent/runs", headers=auth_headers(self.actor["id"]), json=payload)

        self.assertIn(response.status_code, {400, 422})
        self.assertIn(response.json()["detail"]["code"], {"invalid_request", "validation_error"})

    def test_agent_api_does_not_expose_generic_tool_execution_or_direct_imports(self) -> None:
        route_paths = {route.path for route in agent_api.router.routes}
        source = inspect.getsource(agent_api)

        self.assertNotIn("/tools", route_paths)
        self.assertNotIn("ToolExecutionRequest", source)
        self.assertNotIn("AgentToolExecutor", source)
        self.assertNotIn("HealthProfile", source)
        self.assertNotIn("BloodPressureRecord", source)
        self.assertNotIn("SymptomRecord", source)
        self.assertNotIn("MedicalDocument", source)
        self.assertNotIn("LLM", source)

    def _payload(
        self,
        *,
        target_user_id: str,
        family_id: str | None = None,
        workflow_type: str = "daily_health_brief",
        user_message: str = "Please summarize my system records.",
        confirmation: bool = False,
        workflow_payload: dict | None = None,
    ) -> dict:
        payload = {
            "target_user_id": target_user_id,
            "workflow_type": workflow_type,
            "user_message": user_message,
            "source": "api_test",
            "confirmation": confirmation,
        }
        if family_id is not None:
            payload["family_id"] = family_id
        if workflow_payload is not None:
            payload["workflow_payload"] = workflow_payload
        return payload

    def _alert_payload(self) -> dict:
        return {
            "title": "Follow-up reminder",
            "description": "Prepare materials before the planned visit.",
            "alert_type": "medical_follow_up",
            "level": "info",
            "suggested_action": "Review system records before the appointment.",
        }

    def _draft_counts(self) -> dict[str, int]:
        with SessionLocal() as db:
            return {
                "health_record_drafts": db.query(HealthRecordDraft).count(),
                "symptom_records": db.query(SymptomRecord).count(),
                "medical_event_drafts": db.query(MedicalEventDraft).count(),
                "medical_events": db.query(MedicalEvent).count(),
                "alerts": db.query(Alert).count(),
            }


if __name__ == "__main__":
    unittest.main()
