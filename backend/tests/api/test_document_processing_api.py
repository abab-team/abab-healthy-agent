from __future__ import annotations

import unittest

from sqlalchemy import func, select

from tests.api.helpers import (
    SessionLocal,
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)
from app.modules.medical_timeline.models import MedicalEvent


class DocumentProcessingApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("processing_owner")
        self.member = create_user("processing_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")
        self.document = self._post_my_document().json()

    def test_create_job_and_mark_status_without_running_ocr_or_llm(self) -> None:
        job = self._create_my_job().json()
        started = client.post(f"/api/v1/document-processing/me/jobs/{job['id']}/started", headers=auth_headers(self.owner["id"]))
        success = client.post(f"/api/v1/document-processing/me/jobs/{job['id']}/success", headers=auth_headers(self.owner["id"]))
        failed = client.post(
            f"/api/v1/document-processing/me/jobs/{job['id']}/failed",
            headers=auth_headers(self.owner["id"]),
            json={"error_message": "manual failure marker"},
        )

        self.assertEqual(job["status"], "pending")
        self.assertEqual(started.json()["status"], "processing")
        self.assertEqual(success.json()["status"], "success")
        self.assertEqual(failed.json()["status"], "failed")

    def test_save_extraction_result_does_not_create_medical_event_or_return_full_raw_text(self) -> None:
        raw = "x" * 240
        response = client.post(
            f"/api/v1/document-processing/me/documents/{self.document['id']}/extraction-results",
            headers=auth_headers(self.owner["id"]),
            json={"ai_summary": "draft only", "raw_extracted_text": raw},
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("raw_extracted_text", response.json())
        self.assertLess(len(response.json()["raw_text_excerpt"]), len(raw))
        self.assertEqual(self._medical_event_count(), 0)

    def test_create_confirm_cancel_event_drafts(self) -> None:
        draft = self._create_my_draft({"medical_event": {"event_type": "checkup", "title": "Confirmed event"}}).json()
        pending = client.get("/api/v1/document-processing/me/event-drafts/pending", headers=auth_headers(self.owner["id"]))
        confirmed = client.post(f"/api/v1/document-processing/me/event-drafts/{draft['id']}/confirm", headers=auth_headers(self.owner["id"]))
        repeat = client.post(f"/api/v1/document-processing/me/event-drafts/{draft['id']}/confirm", headers=auth_headers(self.owner["id"]))
        cancel_draft = self._create_my_draft({"medical_event": {"title": "Cancel me"}}).json()
        cancelled = client.post(f"/api/v1/document-processing/me/event-drafts/{cancel_draft['id']}/cancel", headers=auth_headers(self.owner["id"]))
        cancelled_confirm = client.post(f"/api/v1/document-processing/me/event-drafts/{cancel_draft['id']}/confirm", headers=auth_headers(self.owner["id"]))

        self.assertEqual(len(pending.json()["items"]), 1)
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        self.assertEqual(confirmed.json()["title"], "Confirmed event")
        self.assertEqual(repeat.status_code, 409)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertEqual(cancelled_confirm.status_code, 409)

    def test_invalid_draft_confirmation_returns_bad_request(self) -> None:
        draft = client.post(
            "/api/v1/document-processing/me/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json={"draft_event_type": "checkup", "draft_json": {"medical_event": {"event_type": "checkup"}}},
        ).json()
        response = client.post(f"/api/v1/document-processing/me/event-drafts/{draft['id']}/confirm", headers=auth_headers(self.owner["id"]))

        self.assertEqual(response.status_code, 400)

    def test_event_draft_rejects_cross_scope_document_references(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        family_doc = self._post_family_document().json()
        my_cross_scope_draft = client.post(
            "/api/v1/document-processing/me/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"title": "Wrong scope"}}, family_doc["id"]),
        )
        family_cross_scope_draft = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"title": "Wrong scope"}}, self.document["id"]),
        )

        self.assertEqual(my_cross_scope_draft.status_code, 404)
        self.assertEqual(family_cross_scope_draft.status_code, 404)

    def test_event_draft_rejects_cross_scope_extraction_result_references(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        my_extraction = client.post(
            f"/api/v1/document-processing/me/documents/{self.document['id']}/extraction-results",
            headers=auth_headers(self.owner["id"]),
            json={"ai_summary": "owner draft"},
        ).json()
        family_doc = self._post_family_document().json()
        family_job = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/documents/{family_doc['id']}/jobs",
            headers=auth_headers(self.owner["id"]),
            json={"job_type": "ai_extract"},
        ).json()
        family_extraction = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/extraction-results",
            headers=auth_headers(self.owner["id"]),
            json={"processing_job_id": family_job["id"], "ai_summary": "family draft"},
        ).json()
        my_cross_scope_draft = client.post(
            "/api/v1/document-processing/me/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"title": "Wrong scope"}}, extraction_result_id=family_extraction["id"]),
        )
        family_cross_scope_draft = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"title": "Wrong scope"}}, extraction_result_id=my_extraction["id"]),
        )

        self.assertEqual(my_cross_scope_draft.status_code, 404)
        self.assertEqual(family_cross_scope_draft.status_code, 404)

    def test_family_confirm_requires_documents_and_medical_event_create_permissions(self) -> None:
        denied = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"title": "Denied"}}),
        )
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        family_doc = self._post_family_document().json()
        job = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/documents/{family_doc['id']}/jobs",
            headers=auth_headers(self.owner["id"]),
            json={"job_type": "ai_extract"},
        ).json()
        extraction = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/extraction-results",
            headers=auth_headers(self.owner["id"]),
            json={"processing_job_id": job["id"], "ai_summary": "draft"},
        )
        draft = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/event-drafts",
            headers=auth_headers(self.owner["id"]),
            json=self._draft_payload({"medical_event": {"event_type": "checkup", "title": "Family confirmed"}}, family_doc["id"], extraction.json()["id"]),
        ).json()
        confirmed = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/document-processing/event-drafts/{draft['id']}/confirm",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(extraction.status_code, 201, extraction.text)
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        self.assertEqual(confirmed.json()["user_id"], self.member["id"])

    def _post_my_document(self):
        return client.post(
            "/api/v1/documents/me",
            headers=auth_headers(self.owner["id"]),
            json={"document_type": "checkup_report", "title": "Checkup", "file_name": "checkup.pdf", "file_path": "private/checkup.pdf"},
        )

    def _post_family_document(self):
        return client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
            headers=auth_headers(self.owner["id"]),
            json={"document_type": "checkup_report", "title": "Family checkup", "file_name": "family.pdf", "file_path": "private/family.pdf"},
        )

    def _create_my_job(self):
        return client.post(
            f"/api/v1/document-processing/me/documents/{self.document['id']}/jobs",
            headers=auth_headers(self.owner["id"]),
            json={"job_type": "ai_extract"},
        )

    def _create_my_draft(self, draft_json):
        return client.post("/api/v1/document-processing/me/event-drafts", headers=auth_headers(self.owner["id"]), json=self._draft_payload(draft_json))

    def _draft_payload(self, draft_json, source_document_id=None, extraction_result_id=None):
        payload = {"draft_event_type": "checkup", "draft_title": "Draft", "draft_json": draft_json}
        if source_document_id is not None:
            payload["source_document_id"] = source_document_id
        if extraction_result_id is not None:
            payload["extraction_result_id"] = extraction_result_id
        return payload

    def _medical_event_count(self) -> int:
        with SessionLocal() as db:
            return db.scalar(select(func.count()).select_from(MedicalEvent))


if __name__ == "__main__":
    unittest.main()
