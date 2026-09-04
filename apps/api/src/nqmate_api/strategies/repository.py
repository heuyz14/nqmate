from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.strategies.models import Strategy


class StrategyRepository(Protocol):
    def create(self, strategy: Strategy) -> dict[str, Any]: ...
    def list(self, active: bool | None = None) -> Sequence[dict[str, Any]]: ...


class SupabaseStrategyRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseStrategyRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def create(self, strategy: Strategy) -> dict[str, Any]:
        response = self.client.table("strategies").insert({
            "name": strategy.name, "description": strategy.description,
            "allowed_regimes": list(strategy.allowed_regimes), "required_conditions": list(strategy.required_conditions),
            "confirmation_conditions": list(strategy.confirmation_conditions), "invalidation_conditions": list(strategy.invalidation_conditions),
            "entry_logic": strategy.entry_logic, "target_logic": strategy.target_logic,
            "stop_logic": strategy.stop_logic, "active": strategy.active,
        }).execute()
        return (response.data or [{}])[0]

    def list(self, active: bool | None = None) -> Sequence[dict[str, Any]]:
        query = self.client.table("strategies").select("*").order("created_at", desc=True)
        if active is not None:
            query = query.eq("active", active)
        return query.execute().data or []
