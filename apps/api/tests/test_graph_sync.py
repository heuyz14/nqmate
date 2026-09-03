import unittest
from datetime import date

from jobs.sync_graph import sync_sessions
from nqmate_api.graph.ontology import RegimeDimensions
from nqmate_api.market.models import MarketContract, MarketSession


def stored_session(day: date) -> MarketSession:
    return MarketSession(
        day, 100, 110, 90, 105, 100, 104, 98, 101, 107, 91, 104,
        0, 0.0, 0.0, 5, 2, MarketContract("NQ", "NQU6", "NQ_CONT"),
    )


class GraphSyncTests(unittest.TestCase):
    def test_sync_job_initializes_schema_and_skips_missing_sessions(self) -> None:
        class FakeMarket:
            def get_session(self, day):
                return stored_session(day) if day == date(2026, 9, 2) else None

        class FakeGraph:
            def __init__(self):
                self.schema_calls = 0
                self.synced = []

            def ensure_schema(self):
                self.schema_calls += 1

            def sync_session(self, session_date, dimensions: RegimeDimensions):
                self.synced.append((session_date, dimensions))

        graph = FakeGraph()
        count = sync_sessions(date(2026, 9, 1), date(2026, 9, 3), FakeMarket(), graph)

        self.assertEqual(count, 1)
        self.assertEqual(graph.schema_calls, 1)
        self.assertEqual(graph.synced[0][0], "2026-09-02")
