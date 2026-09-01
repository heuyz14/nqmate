from typing import Any


def health_payload(database: str = "unknown", graph: str = "unknown") -> dict[str, Any]:
    return {"status": "ok", "services": {"database": database, "graph": graph}}

