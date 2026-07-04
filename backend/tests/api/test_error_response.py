from __future__ import annotations

import unittest
import uuid

from fastapi.testclient import TestClient

from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)
from app.main import app
from app.modules.document_center.exceptions import MedicalDocumentNotFoundError


@app.get("/__test__/phase06b/internal-error")
def _phase06b_internal_error():
    raise RuntimeError("select * from C:\\secret\\file_path raw_extracted_text traceback")


@app.get("/__test__/phase06b/business-not-found")
def _phase06b_business_not_found():
    raise MedicalDocumentNotFoundError("private/file_path/raw_extracted_text")


class ApiErrorResponseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()

    def test_missing_current_user_uses_standard_error_shape(self) -> None:
        response = client.get("/api/v1/identity/me")

        self.assertEqual(response.status_code, 401, response.text)
        self.assert_error_detail(response.json(), "missing_current_user")
        self.assertNotIn("token", response.text.lower())

    def test_invalid_current_user_id_returns_safe_bad_request(self) -> None:
        response = client.get("/api/v1/identity/me", headers={"X-Current-User-Id": "not-a-uuid"})

        self.assertEqual(response.status_code, 400, response.text)
        self.assert_error_detail(response.json(), "invalid_request")
        self.assertNotIn("traceback", response.text.lower())

    def test_validation_error_does_not_echo_sensitive_field_values(self) -> None:
        user = create_user("phase06b_validation")

        response = client.patch(
            "/api/v1/identity/me/profile",
            headers=auth_headers(user["id"]),
            json={
                "password_hash": "super-secret-password-hash",
                "status": "inactive",
                "email": "new@example.com",
                "phone": "123",
            },
        )

        self.assertEqual(response.status_code, 422, response.text)
        detail = self.assert_error_detail(response.json(), "validation_error")
        self.assertIsInstance(detail["fields"], list)
        self.assertNotIn("super-secret-password-hash", response.text)
        self.assertNotIn("password_hash", response.text)

    def test_permission_denied_uses_safe_standard_error(self) -> None:
        owner = create_user("phase06b_guard_owner")
        member = create_user("phase06b_guard_member")
        family = create_family(owner["id"])["family"]
        add_member(family["id"], owner["id"], member["id"], "parent", "Parent")
        create_permission_for_member(family["id"], member["id"], share_all=False)

        response = client.get(
            f"/api/v1/families/{family['id']}/members/{member['id']}/documents",
            headers=auth_headers(owner["id"]),
        )

        self.assertEqual(response.status_code, 403, response.text)
        self.assert_error_detail(response.json(), "permission_denied")
        self.assertNotIn("file_path", response.text)
        self.assertNotIn("raw_extracted_text", response.text)

    def test_not_found_response_is_generic(self) -> None:
        response = client.get(f"/api/v1/identity/users/{uuid.uuid4()}")

        self.assertEqual(response.status_code, 404, response.text)
        detail = self.assert_error_detail(response.json(), "resource_not_found")
        self.assertEqual(detail["message"], "The resource was not found or you do not have access to it.")
        self.assertNotIn("user not found", response.text.lower())

    def test_conflict_response_uses_standard_shape(self) -> None:
        payload = {"email": "phase06b.conflict@example.com", "nickname": "First"}
        self.assertEqual(client.post("/api/v1/identity/users", json=payload).status_code, 201)

        response = client.post("/api/v1/identity/users", json=payload)

        self.assertEqual(response.status_code, 409, response.text)
        self.assert_error_detail(response.json(), "conflict")
        self.assertNotIn("password", response.text.lower())

    def test_document_errors_do_not_expose_paths_or_raw_text(self) -> None:
        user = create_user("phase06b_doc")
        raw_text = "raw_extracted_text should not leak"

        response = client.post(
            f"/api/v1/document-processing/me/documents/{uuid.uuid4()}/extraction-results",
            headers=auth_headers(user["id"]),
            json={"ai_summary": "draft", "raw_extracted_text": raw_text},
        )

        self.assertEqual(response.status_code, 404, response.text)
        self.assert_error_detail(response.json(), "resource_not_found")
        self.assertNotIn(raw_text, response.text)
        self.assertNotIn("file_path", response.text)
        self.assertNotIn("raw_extracted_text", response.text)

    def test_business_exception_handler_returns_safe_error(self) -> None:
        local_client = TestClient(app, raise_server_exceptions=False)

        response = local_client.get("/__test__/phase06b/business-not-found")

        self.assertEqual(response.status_code, 404, response.text)
        self.assert_error_detail(response.json(), "resource_not_found")
        self.assertNotIn("file_path", response.text)
        self.assertNotIn("raw_extracted_text", response.text)

    def test_unhandled_exception_response_hides_internal_details(self) -> None:
        local_client = TestClient(app, raise_server_exceptions=False)

        response = local_client.get("/__test__/phase06b/internal-error")

        self.assertEqual(response.status_code, 500, response.text)
        self.assert_error_detail(response.json(), "internal_server_error")
        lowered = response.text.lower()
        self.assertNotIn("traceback", lowered)
        self.assertNotIn("select *", lowered)
        self.assertNotIn("file_path", lowered)
        self.assertNotIn("raw_extracted_text", lowered)

    def assert_error_detail(self, body: dict, code: str) -> dict:
        self.assertIn("detail", body)
        detail = body["detail"]
        self.assertEqual(detail["code"], code)
        self.assertIsInstance(detail["message"], str)
        self.assertIn("request_id", detail)
        self.assertIn("fields", detail)
        return detail


if __name__ == "__main__":
    unittest.main()
