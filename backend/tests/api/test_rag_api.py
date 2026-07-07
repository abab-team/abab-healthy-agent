from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from uuid import UUID

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

from app.core.config import get_settings
from app.modules.health_data.models import BloodPressureRecord


class RagApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["RAG_ENABLED"] = "true"
        get_settings.cache_clear()
        reset_database()
        self.actor = create_user("rag_actor", nickname="Rag Actor")
        self.target = create_user("rag_target", nickname="Rag Target")
        self.family = create_family(self.actor["id"])["family"]
        add_member(self.family["id"], self.actor["id"], self.target["id"], "member", "Target")
        create_permission_for_member(self.family["id"], self.actor["id"], share_all=True)
        create_permission_for_member(self.family["id"], self.target["id"], share_all=True)
        with SessionLocal() as db:
            db.add(
                BloodPressureRecord(
                    user_id=UUID(self.target["id"]),
                    systolic=118,
                    diastolic=76,
                    pulse=72,
                    measured_at=datetime.now(timezone.utc),
                )
            )
            db.commit()

    def tearDown(self) -> None:
        os.environ.pop("RAG_ENABLED", None)
        get_settings.cache_clear()

    def test_search_self_returns_safe_sources(self) -> None:
        response = client.post(
            "/api/v1/rag/search",
            headers=auth_headers(self.target["id"]),
            json={"query": "blood pressure", "target_user_id": self.target["id"], "source_types": ["blood_pressure_summary"]},
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["result_count"], 1)
        self.assertEqual(body["results"][0]["source_type"], "blood_pressure_summary")
        self.assertNotIn("file_path", response.text)
        self.assertNotIn("raw_extracted_text", response.text)

    def test_family_search_requires_allowed_permission(self) -> None:
        patch_response = client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.target['id']}/permissions",
            headers=auth_headers(self.actor["id"]),
            json={
                "share_all": False,
                "can_view_profile": False,
                "can_view_metrics": False,
                "reason": "rag denied test",
            },
        )
        self.assertEqual(patch_response.status_code, 200, patch_response.text)

        response = client.post(
            "/api/v1/rag/search",
            headers=auth_headers(self.actor["id"]),
            json={
                "query": "blood pressure",
                "target_user_id": self.target["id"],
                "family_id": self.family["id"],
                "source_types": ["blood_pressure_summary"],
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "permission_denied")
        self.assertNotIn("118", response.text)

    def test_unknown_source_type_is_rejected(self) -> None:
        response = client.post(
            "/api/v1/rag/search",
            headers=auth_headers(self.actor["id"]),
            json={"query": "demo", "source_types": ["external_medical_article"]},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()
