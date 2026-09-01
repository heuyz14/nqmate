import unittest

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


if __name__ == "__main__":
    unittest.main()
