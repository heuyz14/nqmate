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
