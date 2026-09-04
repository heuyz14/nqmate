from __future__ import annotations

from typing import Any, Protocol

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.strategies.setups import SetupOccurrence


class SetupRepository(Protocol):
    def upsert(self, occurrence: SetupOccurrence) -> dict[str, Any]: ...


class SupabaseSetupRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseSetupRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert(self, occurrence: SetupOccurrence) -> dict[str, Any]:
        response = self.client.table("strategy_setups").upsert({
            "strategy_id": occurrence.strategy_id, "session_date": occurrence.session_date,
            "trigger_at": occurrence.trigger_at.isoformat(), "conditions": list(occurrence.conditions),
        }, on_conflict="strategy_id,session_date").execute()
        return (response.data or [{}])[0]
