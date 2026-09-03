import unittest
from datetime import datetime, timezone

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.analogues.service import rank_analogues


class AnalogueTests(unittest.TestCase):
    def test_ranking_is_deterministic_and_excludes_future_data(self) -> None:
        now = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)
        current = {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}
        history = [
            HistoricalSession("2026-09-01", {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}, now, {"return_30m": 1.0}),
            HistoricalSession("2026-09-02", {"overnight_return": 0.9, "gap": 0.8, "strength": 0.7}, now, {"return_30m": -1.0}),
            HistoricalSession("2026-09-04", {"overnight_return": 0.1, "gap": 0.2, "strength": 0.3}, now, {"return_30m": 5.0}),
        ]
        result = rank_analogues("2026-09-03", current, history, now, top_k=2)
        self.assertEqual([match.session_date for match in result], ["2026-09-01", "2026-09-02"])
        self.assertEqual(result, rank_analogues("2026-09-03", current, history, now, top_k=2))

    def test_missing_features_are_not_imputed(self) -> None:
        now = datetime.now(timezone.utc)
        history = [HistoricalSession("2026-09-01", {"gap": 0.1}, now, {})]
        self.assertEqual(rank_analogues("2026-09-03", {"gap": 0.1, "strength": 0.2}, history, now), [])

    def test_outcomes_are_aggregated(self) -> None:
        now = datetime.now(timezone.utc)
        history = [
            HistoricalSession("2026-09-01", {"gap": 0.1}, now, {"return_30m": 1.0, "onh_first": True}),
            HistoricalSession("2026-09-02", {"gap": 0.2}, now, {"return_30m": -1.0, "onh_first": False}),
        ]
        result = rank_analogues("2026-09-03", {"gap": 0.15}, history, now, top_k=2)
        self.assertEqual(result[0].outcome_summary["return_30m_mean"], 0.0)
        self.assertEqual(result[0].outcome_summary["onh_first_rate"], 0.5)
