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


class HealthDataApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("data_owner")
        self.member = create_user("data_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(
            self.family["id"],
            self.owner["id"],
            self.member["id"],
            "parent",
            "Parent",
        )

    def test_create_my_metric(self) -> None:
        response = self._post_my_metric()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["metric_type"], "steps")

    def test_create_metric_requires_value(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/metrics",
            headers=auth_headers(self.owner["id"]),
            json={"metric_type": "steps"},
        )

        self.assertEqual(response.status_code, 422)

    def test_create_metric_rejects_generic_blood_pressure(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/metrics",
            headers=auth_headers(self.owner["id"]),
            json={"metric_type": "blood_pressure", "value_numeric": 120},
        )

        self.assertEqual(response.status_code, 422)

    def test_get_recent_metrics_supports_comma_query(self) -> None:
        self._post_my_metric()

        response = client.get(
            "/api/v1/health-data/me/metrics/recent?metric_types=steps,weight",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_get_latest_metrics(self) -> None:
        self._post_my_metric()

        response = client.get(
            "/api/v1/health-data/me/metrics/latest?metric_types=steps",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["steps"]["value_numeric"], 1000.0)

    def test_get_metric_summary(self) -> None:
        self._post_my_metric()

        response = client.get(
            "/api/v1/health-data/me/metrics/steps/summary",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["count"], 1)

    def test_get_my_archive_trends(self) -> None:
        self._post_my_metric()
        self._post_my_blood_pressure()

        response = client.get(
            "/api/v1/health-data/me/archive/trends?metric_types=steps,weight&days=90",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["generated_from"], "system_records")
        self.assertGreaterEqual(len(body["series"]), 3)
        self.assertIn("doctor", body["disclaimer"].lower())
        self.assertNotIn("diagnosis", str(body).lower())

    def test_import_preview_does_not_write_records(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/imports/preview",
            headers=auth_headers(self.owner["id"]),
            json={
                "import_type": "csv",
                "file_name": "demo-health.csv",
                "rows": [
                    {
                        "metric_type": "steps",
                        "measured_at": "2026-07-01T08:00:00Z",
                        "value_numeric": 4200,
                        "unit": "steps",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body["will_write"])
        self.assertEqual(body["valid_count"], 1)
        recent = client.get(
            "/api/v1/health-data/me/metrics/recent?metric_types=steps",
            headers=auth_headers(self.owner["id"]),
        )
        self.assertEqual(recent.json()["items"], [])

    def test_import_confirm_requires_confirmation(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/imports/confirm",
            headers=auth_headers(self.owner["id"]),
            json={
                "confirmation": False,
                "import_type": "csv",
                "rows": [
                    {
                        "metric_type": "weight",
                        "measured_at": "2026-07-01T08:00:00Z",
                        "value_numeric": 62.5,
                        "unit": "kg",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body["will_write"])
        self.assertEqual(body["created_records_count"], 0)

    def test_import_confirm_writes_valid_rows_and_skips_invalid(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/imports/confirm",
            headers=auth_headers(self.owner["id"]),
            json={
                "confirmation": True,
                "import_type": "csv",
                "file_name": "demo-health.csv",
                "rows": [
                    {
                        "metric_type": "weight",
                        "measured_at": "2026-07-01T08:00:00Z",
                        "value_numeric": 62.5,
                        "unit": "kg",
                    },
                    {
                        "metric_type": "unsupported_metric",
                        "measured_at": "2026-07-01T08:00:00Z",
                        "value_numeric": 1,
                    },
                ],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["will_write"])
        self.assertEqual(body["created_records_count"], 1)
        self.assertEqual(body["invalid_count"], 1)

    def test_create_my_blood_pressure(self) -> None:
        response = self._post_my_blood_pressure()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["systolic"], 120)

    def test_create_blood_pressure_rejects_out_of_range(self) -> None:
        response = client.post(
            "/api/v1/health-data/me/blood-pressure",
            headers=auth_headers(self.owner["id"]),
            json={"systolic": 400, "diastolic": 80},
        )

        self.assertEqual(response.status_code, 400)

    def test_get_recent_blood_pressure(self) -> None:
        self._post_my_blood_pressure()

        response = client.get(
            "/api/v1/health-data/me/blood-pressure/recent",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_family_member_recent_metrics_allowed(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-data/metrics",
            headers=auth_headers(self.owner["id"]),
            json={"metric_type": "steps", "value_numeric": 3000, "unit": "steps"},
        )

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-data/metrics/recent",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_family_member_create_metric_denied_before_querying_data(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-data/metrics",
            headers=auth_headers(self.owner["id"]),
            json={"metric_type": "steps", "value_numeric": 3000, "unit": "steps"},
        )

        self.assertEqual(response.status_code, 403)
        recent = client.get(
            "/api/v1/health-data/me/metrics/recent",
            headers=auth_headers(self.member["id"]),
        )
        self.assertEqual(recent.json()["items"], [])

    def test_family_member_create_blood_pressure_allowed(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-data/blood-pressure",
            headers=auth_headers(self.owner["id"]),
            json={"systolic": 118, "diastolic": 76, "pulse": 70},
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["user_id"], self.member["id"])

    def _post_my_metric(self):
        return client.post(
            "/api/v1/health-data/me/metrics",
            headers=auth_headers(self.owner["id"]),
            json={"metric_type": "steps", "value_numeric": 1000, "unit": "steps"},
        )

    def _post_my_blood_pressure(self):
        return client.post(
            "/api/v1/health-data/me/blood-pressure",
            headers=auth_headers(self.owner["id"]),
            json={"systolic": 120, "diastolic": 80, "pulse": 72},
        )


if __name__ == "__main__":
    unittest.main()
