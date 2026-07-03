from __future__ import annotations

import unittest

from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class DocumentCenterApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("doc_owner")
        self.member = create_user("doc_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")

    def test_create_list_detail_and_version_do_not_return_file_path(self) -> None:
        created = self._post_my_document()
        document_id = created.json()["id"]
        listed = client.get("/api/v1/documents/me", headers=auth_headers(self.owner["id"]))
        detail = client.get(f"/api/v1/documents/me/{document_id}", headers=auth_headers(self.owner["id"]))
        version = client.post(
            f"/api/v1/documents/me/{document_id}/versions",
            headers=auth_headers(self.owner["id"]),
            json={"file_name": "v2.pdf", "file_path": "private/v2.pdf"},
        )

        self.assertEqual(created.status_code, 201, created.text)
        for body in (created.json(), listed.json()["items"][0], detail.json(), version.json()):
            self.assertNotIn("file_path", body)

    def test_mark_processing_and_confirmed(self) -> None:
        document_id = self._post_my_document().json()["id"]

        processing = client.post(f"/api/v1/documents/me/{document_id}/mark-processing", headers=auth_headers(self.owner["id"]))
        confirmed = client.post(f"/api/v1/documents/me/{document_id}/mark-confirmed", headers=auth_headers(self.owner["id"]))

        self.assertEqual(processing.json()["ai_extract_status"], "processing")
        self.assertEqual(confirmed.json()["ai_extract_status"], "confirmed")

    def test_family_documents_allowed_and_denied(self) -> None:
        denied = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
            headers=auth_headers(self.owner["id"]),
            json=self._document_payload("denied.pdf"),
        )
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        personal = client.post("/api/v1/documents/me", headers=auth_headers(self.member["id"]), json=self._document_payload("member-personal.pdf"))
        created = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
            headers=auth_headers(self.owner["id"]),
            json=self._document_payload("family.pdf"),
        )
        listed = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(personal.status_code, 201, personal.text)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertNotIn("file_path", created.json())
        self.assertEqual(len(listed.json()["items"]), 1)
        self.assertEqual(listed.json()["items"][0]["file_name"], "family.pdf")

    def _post_my_document(self):
        return client.post("/api/v1/documents/me", headers=auth_headers(self.owner["id"]), json=self._document_payload("checkup.pdf"))

    def _document_payload(self, file_name):
        return {"document_type": "checkup_report", "title": "Checkup", "file_name": file_name, "file_path": f"private/{file_name}"}


if __name__ == "__main__":
    unittest.main()
