from urllib.parse import urlparse
from typing import Any

import httpx
from neo4j import GraphDatabase

from nqmate_api.config import Settings


def health_payload(database: str = "unknown", graph: str = "unknown") -> dict[str, Any]:
    return {"status": "ok", "services": {"database": database, "graph": graph}}


def check_supabase(settings: Settings) -> str:
    parsed = urlparse(settings.supabase_url)
    if parsed.scheme != "https" or not parsed.hostname or not settings.supabase_service_key:
        return "not_configured"
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/settings",
            headers={"apikey": settings.supabase_service_key},
            timeout=5,
        )
        return "connected" if response.status_code < 500 else "unavailable"
    except httpx.HTTPError:
        return "unavailable"


def check_neo4j(settings: Settings) -> str:
    parsed = urlparse(settings.neo4j_uri)
    if not parsed.scheme or not parsed.hostname or not settings.neo4j_password:
        return "not_configured"
    driver = None
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        driver.verify_connectivity()
        return "connected"
    except Exception:
        return "unavailable"
    finally:
        if driver is not None:
            driver.close()
