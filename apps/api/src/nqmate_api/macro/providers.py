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


class FREDProvider:
    """Adapter for FRED observations; ALFRED vintages use the same endpoint."""

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None, base_url: str = "https://api.stlouisfed.org/fred") -> None:
        self._api_key, self._client, self._base_url = api_key, client or httpx.AsyncClient(timeout=30), base_url

    async def fetch(self, series_id: str, realtime_start: str | None = None, realtime_end: str | None = None) -> Sequence[MacroObservation]:
        params: dict[str, Any] = {"api_key": self._api_key, "file_type": "json", "series_id": series_id}
        if realtime_start: params["realtime_start"] = realtime_start
        if realtime_end: params["realtime_end"] = realtime_end
        response = await self._client.get(f"{self._base_url}/series/observations", params=params)
        response.raise_for_status()
        payload = response.json()
        observations = []
        for row in payload.get("observations", []):
            if row.get("value") in (None, "."):
                continue
            vintage = row.get("realtime_start")
            observations.append(MacroObservation(
                series_id=series_id, period=row["date"], value=float(row["value"]),
                released_at=None, retrieved_at=datetime.now(timezone.utc),
                vintage_date=datetime.fromisoformat(vintage).replace(tzinfo=timezone.utc) if vintage else None,
            ))
        return observations


class BEAProvider:
    """Adapter for official BEA public API datasets."""

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None, base_url: str = "https://apps.bea.gov/api/data/") -> None:
        self._api_key, self._client, self._base_url = api_key, client or httpx.AsyncClient(timeout=30), base_url

    async def fetch(self, dataset: str, table: str, line: str, period: str) -> Sequence[MacroObservation]:
        response = await self._client.get(self._base_url, params={
            "UserID": self._api_key, "method": "GETDATA", "datasetname": dataset,
            "TableName": table, "LineNumber": line, "Year": period[:4], "ResultFormat": "JSON",
        })
        response.raise_for_status()
        payload = response.json().get("BEAAPI", {})
        if payload.get("Results", {}).get("Error"):
            raise ValueError("BEA request did not succeed")
        rows = payload.get("Results", {}).get("Data", [])
        return [MacroObservation(
            series_id=f"{dataset}:{table}:{line}", period=row["TimePeriod"], value=float(str(row["DataValue"]).replace(",", "")),
            released_at=None, retrieved_at=datetime.now(timezone.utc), vintage_date=None,
        ) for row in rows if row.get("TimePeriod") == period and row.get("DataValue") not in (None, "")]
