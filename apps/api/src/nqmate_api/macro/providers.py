from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Sequence

import httpx

from nqmate_api.macro.models import MacroObservation, ScheduledRelease


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


class BLSReleaseCalendarProvider:
    """Parse the official BLS iCalendar release schedule."""

    def __init__(self, url: str = "https://www.bls.gov/schedule/news_release/bls.ics", client: httpx.AsyncClient | None = None) -> None:
        self._url, self._client = url, client or httpx.AsyncClient(timeout=30)

    async def fetch(self) -> Sequence[ScheduledRelease]:
        response = await self._client.get(self._url, headers={"User-Agent": "nqmate/0.1 (+https://github.com/heuyz14/nqmate)"})
        response.raise_for_status()
        lines = [line.strip() for line in response.text.splitlines()]
        releases: list[ScheduledRelease] = []
        current: dict[str, str] = {}
        for line in lines + ["END:VEVENT"]:
            if line == "BEGIN:VEVENT":
                current = {}
            elif line == "END:VEVENT" and current:
                if current.get("uid") and current.get("summary") and current.get("dtstart"):
                    releases.append(ScheduledRelease(current["uid"], current["summary"], _parse_ics_datetime(current["dtstart"], current.get("tzid"))))
                current = {}
            elif ":" in line:
                name, value = line.split(":", 1)
                key, *parameters = name.split(";")
                current[key.lower()] = value
                for parameter in parameters:
                    if parameter.startswith("TZID="):
                        current["tzid"] = parameter[5:]
        return releases


def _parse_ics_datetime(value: str, timezone_name: str | None) -> datetime:
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    local = datetime.strptime(value, "%Y%m%dT%H%M%S")
    return local.replace(tzinfo=ZoneInfo(timezone_name or "America/New_York")).astimezone(timezone.utc)


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
