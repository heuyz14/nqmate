from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.config import Settings


class AnalogueRepository(Protocol):
    def upsert(self, session: HistoricalSession) -> None: ...
    def list(self, limit: int = 500) -> Sequence[HistoricalSession]: ...


class SupabaseAnalogueRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseAnalogueRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert(self, session: HistoricalSession) -> None:
        self.client.table("analogue_vectors").upsert({
            "session_date": session.session_date, "features": session.features,
            "outcomes": session.outcomes, "available_at": session.available_at.isoformat(),
            "feature_version": "analogue-v1",
        }, on_conflict="session_date").execute()

    def list(self, limit: int = 500) -> Sequence[HistoricalSession]:
        rows = self.client.table("analogue_vectors").select("*").order(
            "session_date", desc=True
        ).limit(min(limit, 1000)).execute().data or []
        return [HistoricalSession(
            row["session_date"], row["features"], datetime.fromisoformat(row["available_at"].replace("Z", "+00:00")), row.get("outcomes") or {},
        ) for row in rows]
