from __future__ import annotations

import unittest

from tests.api.helpers import auth_headers, client, create_user, reset_database


class ApiInputValidationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user = create_user("phase06c_input")
        self.headers = auth_headers(self.user["id"])

    def test_unknown_sensitive_fields_are_rejected_without_echoing_names_or_values(self) -> None:
        response = client.post(
            "/api/v1/identity/users",
            json={
                "email": "phase06c.sensitive@example.com",
                "password_hash": "super-secret-password-hash",
                "token": "secret-token-value",
                "api_key": "secret-api-key-value",
            },
        )

        self.assert_validation_error(response)
        self.assertNotIn("super-secret-password-hash", response.text)
        self.assertNotIn("secret-token-value", response.text)
        self.assertNotIn("secret-api-key-value", response.text)
        self.assertNotIn("password_hash", response.text)
        self.assertNotIn("api_key", response.text)

    def test_too_long_title_is_rejected(self) -> None:
        response = client.post(
            "/api/v1/documents/me",
            headers=self.headers,
            json=self.document_payload(title="T" * 121),
        )

        self.assert_validation_error(response)

    def test_too_long_raw_text_is_rejected_without_echoing_full_text(self) -> None:
        raw_text = "症状" * 1200
        response = client.post(
            "/api/v1/health-records/me/symptoms",
            headers=self.headers,
            json={"raw_text": raw_text},
        )

        self.assert_validation_error(response)
        self.assertNotIn(raw_text, response.text)

    def test_document_rejects_local_and_unsafe_file_paths(self) -> None:
        unsafe_paths = [
            r"C:\Users\someone\secret.pdf",
            "/home/someone/secret.pdf",
            "../secret.pdf",
            "file:///tmp/secret.pdf",
        ]
        for file_path in unsafe_paths:
            with self.subTest(file_path=file_path):
                response = client.post(
                    "/api/v1/documents/me",
                    headers=self.headers,
                    json=self.document_payload(file_path=file_path),
                )
                self.assert_validation_error(response)
                self.assertNotIn(file_path, response.text)

    def test_demo_file_path_is_allowed_and_response_hides_file_path(self) -> None:
        response = client.post(
            "/api/v1/documents/me",
            headers=self.headers,
            json=self.document_payload(file_path="demo://documents/checkup.pdf"),
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("file_path", response.json())
        self.assertNotIn("demo://documents/checkup.pdf", response.text)

    def test_too_long_raw_extracted_text_is_rejected_without_echoing_content(self) -> None:
        document = client.post(
            "/api/v1/documents/me",
            headers=self.headers,
            json=self.document_payload(file_path="demo://documents/extract.pdf"),
        ).json()
        raw_text = "抽取文本" * 3000

        response = client.post(
            f"/api/v1/document-processing/me/documents/{document['id']}/extraction-results",
            headers=self.headers,
            json={"ai_summary": "draft", "raw_extracted_text": raw_text},
        )

        self.assert_validation_error(response)
        self.assertNotIn(raw_text, response.text)
        self.assertNotIn("raw_extracted_text", response.text)

    def test_days_query_range_is_validated(self) -> None:
        for days in (0, 9999):
            with self.subTest(days=days):
                response = client.get(
                    f"/api/v1/health-data/me/metrics/weight/summary?days={days}",
                    headers=self.headers,
                )
                self.assert_validation_error(response)

    def test_identity_profile_patch_rejects_forbidden_extra_fields(self) -> None:
        response = client.patch(
            "/api/v1/identity/me/profile",
            headers=self.headers,
            json={
                "nickname": "Allowed",
                "status": "inactive",
                "password_hash": "super-secret-password-hash",
                "email": "new@example.com",
                "phone": "123",
            },
        )

        self.assert_validation_error(response)
        self.assertNotIn("super-secret-password-hash", response.text)
        self.assertNotIn("password_hash", response.text)

    def test_alert_empty_title_and_message_are_rejected(self) -> None:
        response = client.post(
            "/api/v1/alerts/me",
            headers=self.headers,
            json={"alert_type": "data_missing", "level": "info", "title": "   ", "message": ""},
        )

        self.assert_validation_error(response)

    def test_symptom_empty_raw_text_is_rejected(self) -> None:
        response = client.post(
            "/api/v1/health-records/me/symptoms",
            headers=self.headers,
            json={"raw_text": "   "},
        )

        self.assert_validation_error(response)

    def document_payload(self, *, title: str = "Checkup", file_path: str = "demo://documents/checkup.pdf") -> dict:
        return {
            "document_type": "checkup_report",
            "title": title,
            "file_name": "checkup.pdf",
            "file_path": file_path,
        }

    def assert_validation_error(self, response) -> None:
        self.assertEqual(response.status_code, 422, response.text)
        body = response.json()
        self.assertIn("detail", body)
        detail = body["detail"]
        self.assertEqual(detail["code"], "validation_error")
        self.assertIsInstance(detail["message"], str)
        self.assertIn("request_id", detail)
        self.assertIsInstance(detail["fields"], list)
        self.assertTrue(detail["fields"])
        for field in detail["fields"]:
            self.assertIn("field", field)
            self.assertIn("type", field)
            self.assertIn("message", field)


if __name__ == "__main__":
    unittest.main()
