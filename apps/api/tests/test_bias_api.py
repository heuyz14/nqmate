import unittest
from fastapi.testclient import TestClient

from nqmate_api.bias.models import BiasResult
from nqmate_api.main import app, get_bias_repository


class BiasApiTests(unittest.TestCase):
    def test_generate_bias_validates_snapshot_and_persists_prediction(self) -> None:
        class FakeRepository:
            def create(self, snapshot, result):
                self.saved = (snapshot, result)
                return {"id": "prediction-1", "direction": result.direction, "score": result.score}

        repository = FakeRepository()
        app.dependency_overrides[get_bias_repository] = lambda: repository
        try:
            response = TestClient(app).post("/api/v1/bias/generate", json={
                "overnightStructure": 0.8, "gap": 0.2, "technicalLocation": 0.6,
                "relativeStrength": 0.4, "macroContext": -0.2, "newsContext": 0.3,
            })
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "prediction-1")
        self.assertEqual(repository.saved[1].direction, "BULLISH")

    def test_generate_bias_rejects_out_of_range_snapshot(self) -> None:
        response = TestClient(app).post("/api/v1/bias/generate", json={
            "overnightStructure": 2, "gap": 0, "technicalLocation": 0,
            "relativeStrength": 0, "macroContext": 0, "newsContext": 0,
        })
        self.assertEqual(response.status_code, 422)
