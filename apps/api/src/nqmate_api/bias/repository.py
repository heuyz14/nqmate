from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.bias.models import BiasResult, BiasSnapshot
from nqmate_api.bias.llm import BiasExplanation
from nqmate_api.config import Settings


class BiasRepository(Protocol):
    def create(self, snapshot: BiasSnapshot, result: BiasResult) -> dict[str, Any]: ...
    def latest(self) -> dict[str, Any] | None: ...
    def history(self, limit: int = 50) -> Sequence[dict[str, Any]]: ...
    def get(self, prediction_id: str) -> dict[str, Any] | None: ...
    def create_explanation(self, prediction_id: str, explanation: BiasExplanation) -> dict[str, Any]: ...


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
            "feature_version": "bias-snapshot-v1", "input_snapshot": asdict(snapshot),
        }).execute()
        return (response.data or [{}])[0]

    def latest(self) -> dict[str, Any] | None:
        response = self.client.table("bias_predictions").select("*").order(
            "created_at", desc=True
        ).limit(1).execute()
        return (response.data or [None])[0]

    def history(self, limit: int = 50) -> Sequence[dict[str, Any]]:
        return self.client.table("bias_predictions").select("*").order(
            "created_at", desc=True
        ).limit(min(limit, 100)).execute().data or []

    def get(self, prediction_id: str) -> dict[str, Any] | None:
        response = self.client.table("bias_predictions").select("*").eq("id", prediction_id).maybe_single().execute()
        return response.data if response and response.data else None

    def create_explanation(self, prediction_id: str, explanation: BiasExplanation) -> dict[str, Any]:
        response = self.client.table("bias_explanations").insert({
            "prediction_id": prediction_id, "direction": explanation.direction,
            "confidence": explanation.confidence, "summary": explanation.summary,
            "bull_case": list(explanation.bull_case), "bear_case": list(explanation.bear_case),
            "invalidation": list(explanation.invalidation), "risks": list(explanation.risks),
        }).execute()
        return (response.data or [{}])[0]
