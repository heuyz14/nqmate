from fastapi import FastAPI

from nqmate_api.config import Settings
from nqmate_api.health import check_neo4j, check_supabase, health_payload

app = FastAPI(title="NQmate API", version="0.1.0")


@app.get("/health", tags=["health"])
async def health() -> dict[str, object]:
    settings = Settings()
    return health_payload(
        database=check_supabase(settings),
        graph=check_neo4j(settings),
    )
