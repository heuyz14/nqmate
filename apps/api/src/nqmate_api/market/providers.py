from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from time import monotonic
from typing import Any, Protocol, Sequence

import httpx

from nqmate_api.market.models import MarketBar, MarketContract


class MarketDataProvider(Protocol):
    async def get_bars(self, ticker: str, start: date, end: date, timeframe: str = "1min") -> Sequence[MarketBar]: ...

    async def get_contract(self, product: str, as_of: date) -> MarketContract: ...

    async def get_market_status(self) -> str: ...

    async def get_latest_price(self, ticker: str) -> float | None: ...


def _timestamp(value: int | float | str) -> datetime:
    numeric = int(value)
    if numeric > 10**17:
        return datetime.fromtimestamp(numeric / 1_000_000_000, timezone.utc)
    if numeric > 10**14:
        return datetime.fromtimestamp(numeric / 1_000_000, timezone.utc)
    if numeric > 10**11:
        return datetime.fromtimestamp(numeric / 1_000, timezone.utc)
    return datetime.fromtimestamp(numeric, timezone.utc)


class MassiveMarketDataProvider:
    """Massive Futures REST adapter; response values are validated into MarketBar."""

    def __init__(self, api_key: str, base_url: str = "https://api.massive.com", client: httpx.AsyncClient | None = None, request_interval_seconds: float = 12.0) -> None:
        if not api_key:
            raise ValueError("Massive API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.request_interval_seconds = request_interval_seconds
        self._last_request_at = 0.0

    async def _get(self, client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
        elapsed = monotonic() - self._last_request_at
        if elapsed < self.request_interval_seconds:
            await asyncio.sleep(self.request_interval_seconds - elapsed)
        for attempt in range(4):
            response = await client.get(url, **kwargs)
            self._last_request_at = monotonic()
            if response.status_code != 429 or attempt == 3:
                return response
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else 12.0 * (attempt + 1)
            await asyncio.sleep(min(delay, 60.0))
        raise RuntimeError("Massive request retry exhausted")

    async def get_bars(self, ticker: str, start: date, end: date, timeframe: str = "1min") -> Sequence[MarketBar]:
        if timeframe != "1min":
            raise ValueError("Phase 1 supports 1min bars only")
        close_client = self.client is None
        client = self.client or httpx.AsyncClient()
        try:
            response = await self._get(client,
                f"{self.base_url}/futures/v1/aggs/{ticker}",
                params={
                    "resolution": timeframe,
                    "window_start.gte": start.isoformat(),
                    # The API's date filter is a candle-start filter. Include the
                    # full end date so the regular session is not truncated at 00:00 UTC.
                    "window_start.lt": (end + timedelta(days=1)).isoformat(),
                    "sort": "window_start.asc",
                    "limit": 50000,
                    "apiKey": self.api_key,
                },
                timeout=30,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            ingested_at = datetime.now(timezone.utc)
            bars: list[MarketBar] = []
            for row in payload.get("results", []):
                timestamp = _timestamp(row["window_start"])
                bars.append(
                    MarketBar(
                        symbol=ticker,
                        timestamp=timestamp,
                        timeframe=timeframe,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0)),
                        provider="massive",
                        ingested_at=ingested_at,
                        available_at=ingested_at,
                    )
                )
            return bars
        finally:
            if close_client:
                await client.aclose()

    async def get_contract(self, product: str, as_of: date) -> MarketContract:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient()
        try:
            response = await self._get(client,
                f"{self.base_url}/futures/v1/contracts",
                params={
                    "product_code": product,
                    "date": as_of.isoformat(),
                    "active": "true",
                    "type": "single",
                    "limit": 1000,
                    "apiKey": self.api_key,
                },
                timeout=30,
            )
            response.raise_for_status()
            rows = response.json().get("results", [])
            if not rows:
                raise LookupError(f"No active {product} contract for {as_of}")
            row = sorted(rows, key=lambda item: item.get("last_trade_date") or "9999-12-31")[0]
            expiration = date.fromisoformat(row["last_trade_date"]) if row.get("last_trade_date") else None
            return MarketContract(
                product=product,
                raw_contract_symbol=row["ticker"],
                continuous_symbol=f"{product}_CONT",
                expiration=expiration,
            )
        finally:
            if close_client:
                await client.aclose()

    async def get_market_status(self) -> str:
        return "unknown"

    async def get_latest_price(self, ticker: str) -> float | None:
        bars = await self.get_bars(ticker, date.today(), date.today())
        return bars[-1].close if bars else None
