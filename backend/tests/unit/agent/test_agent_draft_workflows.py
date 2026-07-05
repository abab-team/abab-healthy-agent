from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase08c_draft_workflows.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import medical_event_draft_create, symptom_draft_create  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.document_processing.models import MedicalEventDraft  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


class AgentDraftWorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase08c.actor.{suffix}@example.com",
            phone=f"p08c_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase08c.target.{suffix}@example.com",
            phone=f"p08c_target_{suffix}",
            nickname="Target",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 08C Family",
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
        self.runtime = AgentRuntime()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_unconfirmed_symptom_workflow_records_blocked_tool_call_without_draft(self) -> None:
        result = self.runtime.run(
            self.db,
            self._request(
                "symptom_draft_create",
                confirmation=False,
                workflow_payload={"raw_text": "Record a mild symptom note."},
            ),
        )

        self.assertEqual(result.workflow_type, "symptom_draft_create")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertIn("requires_confirmation", result.generated_content)
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 0)
        self.assertEqual(self.db.query(SymptomRecord).count(), 0)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].tool_name, "health_record.symptom_draft.create")
        self.assertIn("blocked", calls[0].status.value)

    def test_confirmed_symptom_workflow_creates_pending_draft_only(self) -> None:
        result = self.runtime.run(
            self.db,
            self._request(
                "symptom_draft_create",
                confirmation=True,
                workflow_payload={"raw_text": "Record a mild symptom note."},
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("draft_id=", result.generated_content)
        self.assertIn("formal_record_created=false", result.generated_content)
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 1)
        self.assertEqual(self.db.query(SymptomRecord).count(), 0)

    def test_unconfirmed_medical_event_workflow_records_blocked_tool_call_without_draft(self) -> None:
        result = self.runtime.run(
            self.db,
            self._request(
                "medical_event_draft_create",
                confirmation=False,
                workflow_payload={"draft_title": "Follow-up note", "summary": "User-provided follow-up note."},
            ),
        )

        self.assertEqual(result.workflow_type, "medical_event_draft_create")
        self.assertIn("requires_confirmation", result.generated_content)
        self.assertEqual(self.db.query(MedicalEventDraft).count(), 0)
        self.assertEqual(self.db.query(MedicalEvent).count(), 0)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].tool_name, "document_processing.medical_event_draft.create")
        self.assertIn("blocked", calls[0].status.value)

    def test_confirmed_medical_event_workflow_creates_pending_draft_only(self) -> None:
        result = self.runtime.run(
            self.db,
            self._request(
                "medical_event_draft_create",
                confirmation=True,
                workflow_payload={"draft_title": "Follow-up note", "summary": "User-provided follow-up note."},
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("draft_id=", result.generated_content)
        self.assertIn("formal_event_created=false", result.generated_content)
        self.assertEqual(self.db.query(MedicalEventDraft).count(), 1)
        self.assertEqual(self.db.query(MedicalEvent).count(), 0)

    def test_permission_denied_blocks_family_draft_workflow_without_target_data(self) -> None:
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"share_all": False, "can_create_symptom_records": False},
        )

        result = self.runtime.run(
            self.db,
            self._request(
                "symptom_draft_create",
                confirmation=True,
                workflow_payload={"raw_text": "secret target symptom"},
            ),
        )

        self.assertIn("blocked", result.generated_content.lower())
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 0)
        self.assertNotIn("secret target symptom", result.generated_content)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(calls[0].error_type, "permission_denied")

    def test_family_permission_allowed_draft_workflow_can_execute(self) -> None:
        result = self.runtime.run(
            self.db,
            self._request(
                "symptom_draft_create",
                confirmation=True,
                workflow_payload={"raw_text": "Family member note."},
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 1)

    def test_workflows_do_not_call_llm_or_import_business_repositories(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)
        for module in (symptom_draft_create, medical_event_draft_create):
            source = inspect.getsource(module)
            self.assertNotIn("repository", source)
            self.assertNotIn("SessionLocal", source)
            self.assertNotIn("select(", source)
        self.assertNotIn("app.agent.llm_client", sys.modules)

    def _request(
        self,
        workflow_type: str,
        *,
        confirmation: bool,
        workflow_payload: dict,
    ) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor.id,
            target_user_id=self.target.id,
            family_id=self.family.id,
            workflow_type=workflow_type,
            user_message="Please create a controlled pending draft.",
            source="unit_test",
            confirmation=confirmation,
            workflow_payload=workflow_payload,
        )


if __name__ == "__main__":
    unittest.main()
