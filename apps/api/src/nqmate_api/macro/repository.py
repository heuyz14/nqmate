from __future__ import annotations

from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.macro.models import MacroObservation


class MacroRepository(Protocol):
    def upsert(self, observation: MacroObservation) -> None: ...
    def list(self, series_id: str | None = None, limit: int = 100) -> Sequence[dict[str, Any]]: ...


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


class SupabaseMacroRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseMacroRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert(self, observation: MacroObservation) -> None:
        self.client.table("macro_observations").upsert({
            "source": "bls", "series_id": observation.series_id, "period": observation.period,
            "value": observation.value, "released_at": _iso(observation.released_at),
            "retrieved_at": _iso(observation.retrieved_at), "vintage_date": _iso(observation.vintage_date),
        }, on_conflict="source,series_id,period,vintage_date").execute()

    def list(self, series_id: str | None = None, limit: int = 100) -> Sequence[dict[str, Any]]:
        query = self.client.table("macro_observations").select("*").order("period", desc=True).limit(min(limit, 500))
        if series_id:
            query = query.eq("series_id", series_id)
        return query.execute().data or []
