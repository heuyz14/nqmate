import unittest
from unittest.mock import MagicMock

from nqmate_api.ml.models import DatasetRecord, ModelRecord
from nqmate_api.ml.repository import SupabaseMlRepository


class MlRepositoryTests(unittest.TestCase):
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
