import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from postgrest.exceptions import APIError

from nqmate_api.ml.models import DatasetRecord, ModelRecord, SessionFeatureSnapshot
from nqmate_api.ml.repository import SupabaseMlRepository


class MlRepositoryTests(unittest.TestCase):
    def test_snapshot_insert_preserves_point_in_time_metadata(self) -> None:
        client = MagicMock()
        snapshot = SessionFeatureSnapshot(
            date(2026, 9, 8), datetime(2026, 9, 8, 13, 30, tzinfo=timezone.utc),
            "NQU6", "NQU6", "features-v2", {"gap": 1.25},
            datetime(2026, 9, 8, 13, 29, tzinfo=timezone.utc),
        )
        SupabaseMlRepository(client).create_snapshot(snapshot)
        payload = client.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload["session_date"], "2026-09-08")
        self.assertEqual(payload["features"], {"gap": 1.25})
        self.assertEqual(payload["available_at"], "2026-09-08T13:29:00+00:00")
        self.assertEqual(payload["availability_policy"], "strict")

    def test_identical_snapshot_retry_is_idempotent(self) -> None:
        client = MagicMock()
        snapshot = SessionFeatureSnapshot(
            date(2026, 9, 8), datetime(2026, 9, 8, 13, 30, tzinfo=timezone.utc),
            "NQU6", "NQU6", "features-v2", {"gap": 1.25},
            datetime(2026, 9, 8, 13, 29, tzinfo=timezone.utc),
        )
        table = client.table.return_value
        table.insert.return_value.execute.side_effect = APIError({"code": "23505"})
        query = table.select.return_value
        query.eq.return_value = query
        query.maybe_single.return_value.execute.return_value.data = {
            "session_date": "2026-09-08", "snapshot_timestamp": "2026-09-08T08:30:00-05:00",
            "symbol": "NQU6", "contract": "NQU6", "feature_version": "features-v2",
            "features": {"gap": 1.25}, "available_at": "2026-09-08T13:29:00+00:00",
            "availability_policy": "strict",
        }
        assert SupabaseMlRepository(client).create_snapshot(snapshot)["session_date"] == "2026-09-08"

    def test_dataset_upsert_preserves_version_metadata(self) -> None:
        client = MagicMock()
        SupabaseMlRepository(client).upsert_dataset(DatasetRecord("dataset-v1", "direction_30m", "features-v1", 42, "2026-01-01", "2026-03-01"))
        payload = client.table.return_value.upsert.call_args.args[0]
        self.assertEqual(payload["version"], "dataset-v1")
        self.assertEqual(payload["row_count"], 42)

    def test_model_create_does_not_replace_artifact_identity(self) -> None:
        client = MagicMock()
        model = ModelRecord("logistic-v1", "direction_30m", "logistic_regression", "builtin-1", "features-v1", "dataset-v1", {"accuracy": 0.6}, {"learning_rate": 0.1}, "artifacts/logistic-v1.json", "2026-01-01", "2026-03-01", True)
        SupabaseMlRepository(client).create_model(model)
        payload = client.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload["artifact_path"], "artifacts/logistic-v1.json")
        self.assertEqual(client.table.return_value.insert.call_args.kwargs, {})
