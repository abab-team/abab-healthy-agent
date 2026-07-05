from __future__ import annotations

import inspect
import unittest

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

from app.modules.agent import api as agent_api
from app.modules.document_processing.models import MedicalEventDraft
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

    def _draft_counts(self) -> dict[str, int]:
        with SessionLocal() as db:
            return {
                "health_record_drafts": db.query(HealthRecordDraft).count(),
                "symptom_records": db.query(SymptomRecord).count(),
                "medical_event_drafts": db.query(MedicalEventDraft).count(),
                "medical_events": db.query(MedicalEvent).count(),
            }


if __name__ == "__main__":
    unittest.main()
