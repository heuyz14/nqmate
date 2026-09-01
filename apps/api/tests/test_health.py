import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from nqmate_api.main import app
from nqmate_api.health import health_payload


class HealthPayloadTests(unittest.TestCase):
    def test_health_reports_ok_and_dependency_states(self) -> None:
        self.assertEqual(
            health_payload(database="connected", graph="connected"),
            {
                "status": "ok",
                "services": {"database": "connected", "graph": "connected"},
            },
        )

    @patch("nqmate_api.main.check_supabase", return_value="connected")
    @patch("nqmate_api.main.check_neo4j", return_value="connected")
    def test_health_endpoint_reports_dependency_states(self, neo4j_check, supabase_check) -> None:
        response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "services": {"database": "connected", "graph": "connected"},
            },
        )
        supabase_check.assert_called_once()
        neo4j_check.assert_called_once()


class SettingsTests(unittest.TestCase):
    def test_settings_loads_backend_env_file_from_any_working_directory(self) -> None:
        from pathlib import Path
        from nqmate_api.config import Settings

        settings = Settings()
        env_file = Path(settings.model_config["env_file"])
        self.assertEqual(env_file.name, ".env")
        self.assertEqual(env_file.parent.name, "api")
        self.assertTrue(settings.neo4j_uri)


if __name__ == "__main__":
    unittest.main()
