import unittest

from fastapi.testclient import TestClient

from nqmate_api.main import app, get_strategy_repository


class StrategyApiTests(unittest.TestCase):
    def test_create_strategy_validates_and_persists_structured_rules(self) -> None:
        class FakeRepository:
            def create(self, strategy):
                self.saved = strategy
                return {"id": "strategy-1", "name": strategy.name}

        repository = FakeRepository()
        app.dependency_overrides[get_strategy_repository] = lambda: repository
        try:
            response = TestClient(app).post("/api/v1/strategies", json={
                "name": "ONH Breakout", "entryLogic": "break and retest",
                "targetLogic": "range extension", "stopLogic": "close below ONH",
                "requiredConditions": ["above midpoint"],
            })
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "strategy-1")
        self.assertEqual(repository.saved.required_conditions, ("above midpoint",))

    def test_create_strategy_rejects_blank_logic(self) -> None:
        response = TestClient(app).post("/api/v1/strategies", json={
            "name": "Incomplete", "entryLogic": "", "targetLogic": "target", "stopLogic": "stop",
        })
        self.assertEqual(response.status_code, 422)

    def test_strategy_can_be_retrieved_updated_and_deactivated(self) -> None:
        class FakeRepository:
            def get(self, strategy_id): return {"id": strategy_id, "name": "Test", "active": True}
            def update(self, strategy_id, strategy): return {"id": strategy_id, "name": strategy.name}
            def deactivate(self, strategy_id): return {"id": strategy_id, "active": False}

        app.dependency_overrides[get_strategy_repository] = lambda: FakeRepository()
        try:
            client = TestClient(app)
            self.assertEqual(client.get("/api/v1/strategies/strategy-1").status_code, 200)
            response = client.patch("/api/v1/strategies/strategy-1", json={
                "name": "Updated", "entryLogic": "entry", "targetLogic": "target", "stopLogic": "stop",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.delete("/api/v1/strategies/strategy-1").json()["active"], False)
        finally:
            app.dependency_overrides.clear()
