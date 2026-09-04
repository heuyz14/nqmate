import unittest
from fastapi.testclient import TestClient

from nqmate_api.bias.models import BiasResult
from nqmate_api.main import app, get_bias_repository, get_analogue_repository, get_ml_repository


class BiasApiTests(unittest.TestCase):
    def test_observability_endpoint_returns_coverage(self) -> None:
        class FakeRepository:
            def history(self, limit=50):
                return [{"id": "p1", "model_version": "rules-v1", "feature_version": "f1", "input_snapshot": {"gap": 0.1}}]

            def list_outcomes(self, prediction_id):
                return [{"horizon": "return_5m"}]

        app.dependency_overrides[get_bias_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/bias/observability")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["outcome_count"], 1)
        self.assertEqual(response.json()["model_versions"], ["rules-v1"])
    def test_reconstruction_endpoint_returns_inputs_versions_and_outcomes(self) -> None:
        class FakeRepository:
            def get(self, prediction_id):
                return {"id": prediction_id, "input_snapshot": {"gap": 0.2},
                        "direction": "BULLISH", "model_version": "rules-v1", "feature_version": "bias-snapshot-v1"}

            def list_outcomes(self, prediction_id):
                return [{"horizon": "return_5m", "correct": True}]

        app.dependency_overrides[get_bias_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/bias/p1/reconstruction")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["input_snapshot"]["gap"], 0.2)
        self.assertEqual(response.json()["outcomes"][0]["horizon"], "return_5m")

    def test_ml_comparison_endpoint_returns_gated_candidates(self) -> None:
        class FakeRepository:
            def list_models(self, target=None):
                return [
                    {"name": "majority", "target": "direction_60m", "algorithm": "majority", "metrics": {"accuracy": 0.55, "brier_score": 0.25}},
                    {"name": "xgb", "target": "direction_60m", "algorithm": "xgboost", "metrics": {"accuracy": 0.56, "brier_score": 0.24}},
                ]

        app.dependency_overrides[get_ml_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/ml/models/comparison?target=direction_60m")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["comparisons"]["direction_60m"][0]["eligible"])

    def test_ml_model_registry_endpoint_is_bounded(self) -> None:
        class FakeRepository:
            def list_models(self, target=None):
                return [{"name": "baseline-majority", "target": target or "direction_60m", "active": False}]

        app.dependency_overrides[get_ml_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/ml/models?target=direction_60m")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["models"][0]["active"])

    def test_drift_endpoint_compares_prediction_snapshot_windows(self) -> None:
        class FakeRepository:
            def history(self, limit=50):
                return [{"input_snapshot": {"gap": 0.0}}, {"input_snapshot": {"gap": 0.1}},
                        {"input_snapshot": {"gap": 1.0}}, {"input_snapshot": {"gap": 1.1}}]

        app.dependency_overrides[get_bias_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/bias/drift?limit=4")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["features"]["gap"]["status"], "DRIFT")

    def test_history_evaluation_endpoint_returns_confidence_calibration(self) -> None:
        class FakeRepository:
            def history(self, limit=50):
                return [{"id": "p1", "confidence": 0.8}]

            def list_outcomes(self, prediction_id):
                return [{"horizon": "return_5m", "correct": True}]

        app.dependency_overrides[get_bias_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/bias/evaluation")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["outcome_count"], 1)
        self.assertEqual(response.json()["confidence_calibration"][0]["observed_accuracy"], 1.0)

    def test_evaluation_endpoint_returns_versioned_horizon_summary(self) -> None:
        class FakeRepository:
            def get(self, prediction_id):
                return {"id": prediction_id, "model_version": "rules-v1", "feature_version": "bias-snapshot-v1"}

            def list_outcomes(self, prediction_id):
                return [{"horizon": "return_5m", "realized_return": 0.01, "correct": True}]

        app.dependency_overrides[get_bias_repository] = lambda: FakeRepository()
        try:
            response = TestClient(app).get("/api/v1/bias/p1/evaluation")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["evaluation"]["horizons"]["return_5m"]["accuracy"], 1.0)

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
                "analogueBullRate": 0.8, "analogueAvg60mReturn": 0.0025,
                "analogueSampleSize": 20,
            })
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "prediction-1")
        self.assertEqual(repository.saved[1].direction, "BULLISH")
        self.assertIn("historical analogues favor bullish outcomes (80.0% up)", repository.saved[1].evidence)
        self.assertIn("analogue 60m mean return is +0.25%", repository.saved[1].bull_case)

    def test_generate_bias_rejects_out_of_range_snapshot(self) -> None:
        response = TestClient(app).post("/api/v1/bias/generate", json={
            "overnightStructure": 2, "gap": 0, "technicalLocation": 0,
            "relativeStrength": 0, "macroContext": 0, "newsContext": 0,
        })
        self.assertEqual(response.status_code, 422)

    def test_generate_bias_can_retrieve_analogue_context(self) -> None:
        from datetime import datetime, timezone
        from nqmate_api.analogues.models import HistoricalSession

        class FakeBiasRepository:
            def create(self, snapshot, result):
                self.saved = (snapshot, result)
                return {"id": "prediction-2", "direction": result.direction}

        class FakeAnalogueRepository:
            def list(self, limit=500):
                return [HistoricalSession(
                    "2026-09-02", {"gap": 0.1}, datetime(2026, 9, 2, 12, tzinfo=timezone.utc),
                    {"return_60m": 0.01},
                )]

        bias_repository = FakeBiasRepository()
        app.dependency_overrides[get_bias_repository] = lambda: bias_repository
        app.dependency_overrides[get_analogue_repository] = lambda: FakeAnalogueRepository()
        try:
            response = TestClient(app).post("/api/v1/bias/generate", json={
                "overnightStructure": 0.8, "gap": 0.2, "technicalLocation": 0.6,
                "relativeStrength": 0.4, "macroContext": -0.2, "newsContext": 0.3,
                "analogue": {
                    "sessionDate": "2026-09-03", "features": {"gap": 0.1},
                    "predictionTime": "2026-09-03T12:00:00Z", "topK": 20,
                },
            })
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["analogue_matches"][0]["session_date"], "2026-09-02")
        self.assertIn("historical analogues favor bullish outcomes (100.0% up)", bias_repository.saved[1].evidence)
