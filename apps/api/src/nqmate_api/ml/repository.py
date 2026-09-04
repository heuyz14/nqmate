from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.ml.models import DatasetRecord, ModelRecord


class MlRepository(Protocol):
    def upsert_dataset(self, record: DatasetRecord) -> dict[str, Any]: ...
    def create_model(self, record: ModelRecord) -> dict[str, Any]: ...
    def list_models(self, target: str | None = None) -> Sequence[dict[str, Any]]: ...


class SupabaseMlRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseMlRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert_dataset(self, record: DatasetRecord) -> dict[str, Any]:
        response = self.client.table("ml_datasets").upsert({
            "version": record.version, "target": record.target,
            "feature_version": record.feature_version, "row_count": record.row_count,
            "start_date": record.start_date, "end_date": record.end_date,
        }, on_conflict="version").execute()
        return (response.data or [{}])[0]

    def create_model(self, record: ModelRecord) -> dict[str, Any]:
        response = self.client.table("ml_models").insert({
            "name": record.name, "target": record.target, "algorithm": record.algorithm,
            "algorithm_version": record.algorithm_version, "feature_version": record.feature_version,
            "dataset_version": record.dataset_version, "metrics": record.metrics,
            "hyperparameters": record.hyperparameters, "artifact_path": record.artifact_path,
            "training_start": record.training_start, "training_end": record.training_end,
            "active": record.active,
        }).execute()
        return (response.data or [{}])[0]

    def list_models(self, target: str | None = None) -> Sequence[dict[str, Any]]:
        query = self.client.table("ml_models").select("*").order("created_at", desc=True)
        if target:
            query = query.eq("target", target)
        return query.execute().data or []
