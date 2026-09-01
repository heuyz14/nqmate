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
    gemini_api_key: str | None = None
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_service_key: str | None = Field(default=None, validation_alias="SUPABASE_SERVICE_KEY")
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
