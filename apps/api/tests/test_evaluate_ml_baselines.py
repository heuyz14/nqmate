import unittest
from datetime import datetime, timezone

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.ml.evaluation import dataset_records_for_sessions, rows_from_sessions, target_name


class EvaluateMlBaselineTests(unittest.TestCase):
    def test_rows_use_only_pre_session_features_and_realized_outcome(self) -> None:
        sessions = [HistoricalSession(
            "2026-01-02", {"gap_pct": 0.01, "overnight_return": 0.02},
            datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc), {"return_30m": 0.005},
        )]
        rows = rows_from_sessions(sessions, "return_30m")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].target, 1)
        self.assertEqual(rows[0].features, (0.01, 0.02))

    def test_missing_outcome_is_not_imputed(self) -> None:
        sessions = [HistoricalSession(
            "2026-01-02", {"gap_pct": 0.01},
            datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc), {},
        )]
        self.assertEqual(rows_from_sessions(sessions, "return_30m"), ())

    def test_target_name_is_horizon_specific(self) -> None:
        self.assertEqual(target_name("return_60m"), "direction_60m")
        self.assertEqual(target_name("open_close"), "direction_close")

    def test_dataset_catalog_skips_missing_horizons_without_imputation(self) -> None:
        sessions = [HistoricalSession(
            "2026-01-02", {"gap_pct": 0.01},
            datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc),
            {"return_5m": 0.001, "return_240m": None},
        )]
        records = dataset_records_for_sessions(sessions, datetime(2026, 1, 1).date(), datetime(2026, 1, 2).date())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].target, "direction_5m")
        self.assertEqual(records[0].row_count, 1)
