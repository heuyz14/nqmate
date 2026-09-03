import unittest
from unittest.mock import MagicMock

from nqmate_api.graph.ontology import RegimeDimensions, constraints, sync_session_query
from nqmate_api.graph.repository import Neo4jGraphRepository


class GraphTests(unittest.TestCase):
    def test_ontology_keeps_regime_dimensions_separate(self) -> None:
        dimensions = RegimeDimensions("UP", "HIGH", "GAP_UP", "INSIDE_PRIOR_RANGE", "YIELDS_UP", "PRE_EVENT")
        self.assertEqual(dimensions.as_properties()["overnight_direction"], "UP")
        self.assertEqual(len(constraints()), 3)
        self.assertIn("CLASSIFIED_AS", sync_session_query())

    def test_sync_uses_merge_for_idempotent_semantic_nodes(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value
        repository = Neo4jGraphRepository(driver)
        dimensions = RegimeDimensions("UP", "HIGH", "GAP_UP", "INSIDE_PRIOR_RANGE", "YIELDS_UP", "PRE_EVENT")

        repository.sync_session("2026-09-02", dimensions)

        query = session.run.call_args.args[0]
        self.assertIn("MERGE (market_session:MarketSession", query)
        self.assertIn("MERGE (regime:MarketRegime", query)
        self.assertNotIn("MarketBar", query)
        self.assertEqual(session.run.call_args.kwargs["session_date"], "2026-09-02")

    def test_sync_news_event_stores_semantics_and_mentions_companies(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value

        Neo4jGraphRepository(driver).sync_news_event(
            provider="marketaux", provider_id="article-1", event_type="technology",
            event_timestamp="2026-09-02T13:00:00+00:00", available_at="2026-09-02T13:00:00+00:00",
            relevance=0.9, direction="bullish", themes=("AI",), companies=("NVDA",),
        )

        query = session.run.call_args.args[0]
        self.assertIn("MERGE (event:NewsEvent", query)
        self.assertIn("MENTIONS", query)
        self.assertNotIn("headline", query.lower())

    def test_sync_prediction_links_only_when_session_is_supplied(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value

        Neo4jGraphRepository(driver).sync_prediction(
            "prediction-1", "2026-09-02T14:00:00+00:00", "BULLISH", 0.4, 0.4, "2026-09-02",
        )

        query = session.run.call_args.args[0]
        self.assertIn("MERGE (prediction:Prediction", query)
        self.assertIn("MADE_DURING", query)

    def test_sync_macro_event_keeps_release_metadata_without_raw_observations(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value

        Neo4jGraphRepository(driver).sync_macro_event(
            "fed:rate-1", "FOMC rate decision", "2026-09-02T18:00:00+00:00",
            "2026-09-02T18:00:00+00:00", "HIGH",
        )

        query = session.run.call_args.args[0]
        self.assertIn("MERGE (event:MacroEvent", query)
        self.assertNotIn("MacroObservation", query)

    def test_query_regimes_filters_dimensions_without_candle_access(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value
        session.run.return_value.data.return_value = [{"session_date": "2026-09-02", "regime": {"gap": "GAP_UP"}}]

        result = Neo4jGraphRepository(driver).query_regimes({"gap": "GAP_UP"}, 10)

        query = session.run.call_args.args[0]
        self.assertIn("CLASSIFIED_AS", query)
        self.assertNotIn("MarketBar", query)
        self.assertEqual(result[0]["session_date"], "2026-09-02")

    def test_knowledge_regime_endpoint_passes_only_requested_dimensions(self) -> None:
        from fastapi.testclient import TestClient
        from nqmate_api.main import app, get_graph_repository

        class FakeGraph:
            def query_regimes(self, filters, limit):
                self.args = (filters, limit)
                return [{"session_date": "2026-09-02"}]

        graph = FakeGraph()
        app.dependency_overrides[get_graph_repository] = lambda: graph
        try:
            response = TestClient(app).get("/api/v1/knowledge/regimes?gap=GAP_UP&limit=5")
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(graph.args, ({"gap": "GAP_UP"}, 5))
        self.assertEqual(response.json()["sessions"][0]["session_date"], "2026-09-02")

    def test_sync_outcome_links_to_prediction(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value

        Neo4jGraphRepository(driver).sync_outcome(
            "outcome-1", "prediction-1", "2026-09-02T15:00:00+00:00", "NQ", "60m", 0.004,
        )

        query = session.run.call_args.args[0]
        self.assertIn("MERGE (outcome:Outcome", query)
        self.assertIn("RESULTED_IN", query)

    def test_strategy_evidence_query_traverses_regime_relationship(self) -> None:
        driver = MagicMock()
        session = driver.session.return_value.__enter__.return_value
        session.run.return_value.data.return_value = [{"strategy": "ONH Breakout", "sample_size": 12}]

        result = Neo4jGraphRepository(driver).query_strategy_evidence({"gap": "GAP_UP"}, 10)

        query = session.run.call_args.args[0]
        self.assertIn("PERFORMS_WELL_IN", query)
        self.assertEqual(result[0]["strategy"], "ONH Breakout")
