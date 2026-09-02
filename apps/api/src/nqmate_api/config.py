from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated server-side configuration; secrets never belong in web code."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    massive_api_key: str | None = None
    marketaux_api_key: str | None = None
    fred_api_key: str | None = None
    bls_api_key: str | None = None
    bls_release_calendar_url: str = "https://www.bls.gov/schedule/news_release/bls.ics"
    bea_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    forex_factory_enabled: bool = True
    marketaux_enabled: bool = True
    bls_enabled: bool = True
    federal_reserve_enabled: bool = True
    bea_enabled: bool = True
    news_poll_interval_active: int = 60
    news_poll_interval_idle: int = 300
    news_min_nq_relevance: float = 0.50
    news_high_impact_threshold: float = 0.75
    news_nlp_enabled: bool = False
    forex_factory_calendar_url: str | None = None
    forex_factory_timezone: str = "America/New_York"
    fed_rss_url: str | None = None
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_service_key: str | None = Field(default=None, validation_alias="SUPABASE_SERVICE_KEY")
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
