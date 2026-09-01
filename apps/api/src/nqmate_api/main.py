from fastapi import FastAPI

from nqmate_api.health import health_payload

app = FastAPI(title="NQmate API", version="0.1.0")


@app.get("/health", tags=["health"])
async def health() -> dict[str, object]:
    return health_payload(database="not_configured", graph="not_configured")

