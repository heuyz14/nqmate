from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

import httpx

from nqmate_api.macro.models import MacroObservation


class BLSProvider:
    """Adapter for the official BLS Public Data API v2."""

    def __init__(self, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=30)
        self._url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    async def fetch(self, series_id: str, start_year: int, end_year: int) -> Sequence[MacroObservation]:
        body: dict[str, Any] = {"seriesid": [series_id], "startyear": str(start_year), "endyear": str(end_year)}
        if self._api_key:
            body["registrationkey"] = self._api_key
        response = await self._client.post(self._url, json=body)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError("BLS request did not succeed")
        rows = payload.get("Results", {}).get("series", [])
        if not rows or rows[0].get("seriesID") != series_id:
            raise ValueError("BLS response did not contain the requested series")
        retrieved_at = datetime.now(timezone.utc)
        observations = []
        for row in rows[0].get("data", []):
            period = row.get("period", "")
            if not period.startswith("M") or period == "M13":
                continue
            observations.append(MacroObservation(
                series_id=series_id,
                period=f"{row['year']}-{int(period[1:]):02d}",
                value=float(row["value"]),
                released_at=None,
                retrieved_at=retrieved_at,
                vintage_date=None,
            ))
        return observations
