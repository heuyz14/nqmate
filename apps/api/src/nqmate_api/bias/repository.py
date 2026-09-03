from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.bias.models import BiasResult, BiasSnapshot
from nqmate_api.config import Settings


class BiasRepository(Protocol):
    def create(self, snapshot: BiasSnapshot, result: BiasResult) -> dict[str, Any]: ...
    def latest(self) -> dict[str, Any] | None: ...


class SupabaseBiasRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseBiasRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def create(self, snapshot: BiasSnapshot, result: BiasResult) -> dict[str, Any]:
        response = self.client.table("bias_predictions").insert({
            "direction": result.direction, "score": result.score, "confidence": result.confidence,
            "recommendation": result.recommendation, "catalyst_risk": result.catalyst_risk,
            "evidence": list(result.evidence), "bull_case": list(result.bull_case),
            "bear_case": list(result.bear_case), "invalidation": list(result.invalidation),
            "uncertainty": list(result.uncertainty), "model_version": "rules-v1",
            "feature_version": "bias-snapshot-v1",
        }).execute()
        return (response.data or [{}])[0]

    def latest(self) -> dict[str, Any] | None:
        response = self.client.table("bias_predictions").select("*").order(
            "created_at", desc=True
        ).limit(1).execute()
        return (response.data or [None])[0]
