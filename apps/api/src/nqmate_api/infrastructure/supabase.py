from dataclasses import dataclass


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    service_key: str | None


class SupabaseConnection:
    """Server-side boundary for Supabase; client construction is added with Phase 0 dependencies."""

    def __init__(self, config: SupabaseConfig) -> None:
        self.config = config

