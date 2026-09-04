from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.strategies.outcomes import StrategyOutcome


class OutcomeRepository(Protocol):
    def upsert(self, outcome: StrategyOutcome) -> dict[str, Any]: ...
    def list_for_strategy(self, strategy_id: str) -> Sequence[dict[str, Any]]: ...


class SupabaseOutcomeRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseOutcomeRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert(self, outcome: StrategyOutcome) -> dict[str, Any]:
        response = self.client.table("strategy_outcomes").upsert({
            "setup_id": outcome.setup_id, "strategy_id": outcome.strategy_id,
            "session_date": outcome.session_date, "observed_at": outcome.observed_at.isoformat(),
            "return_pct": outcome.return_pct, "mfe": outcome.mfe, "mae": outcome.mae,
            "regime": outcome.regime,
        }, on_conflict="setup_id").execute()
        return (response.data or [{}])[0]

    def list_for_strategy(self, strategy_id: str) -> Sequence[dict[str, Any]]:
        return self.client.table("strategy_outcomes").select("*").eq(
            "strategy_id", strategy_id
        ).order("observed_at").execute().data or []
