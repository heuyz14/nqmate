from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Protocol, Sequence

from supabase import Client, create_client

from nqmate_api.config import Settings
from nqmate_api.market.models import ContractRollover, MarketBar, MarketContract, MarketSession


class MarketRepository(Protocol):
    def upsert_bars(self, bars: Sequence[MarketBar]) -> int: ...

    def upsert_contract(self, contract: MarketContract) -> None: ...

    def upsert_rollover(self, rollover: ContractRollover) -> None: ...

    def upsert_session(self, session: MarketSession) -> None: ...

    def get_session(self, session_date: date) -> MarketSession | None: ...

    def get_bars(self, start: datetime, end: datetime, symbol: str | None = None) -> Sequence[MarketBar]: ...


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


class SupabaseMarketRepository:
    """Durable market-data persistence; all calls stay server-side."""

    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseMarketRepository":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase configuration is required")
        return cls(create_client(settings.supabase_url, settings.supabase_service_key))

    def upsert_bars(self, bars: Sequence[MarketBar]) -> int:
        if not bars:
            return 0
        payload = [{
            "symbol": bar.symbol,
            "timestamp": _iso(bar.timestamp),
            "timeframe": bar.timeframe,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "provider": bar.provider,
            "ingested_at": _iso(bar.ingested_at),
            "available_at": _iso(bar.available_at),
        } for bar in bars]
        self.client.table("market_bars").upsert(
            payload,
            on_conflict="symbol,timestamp,timeframe,provider",
        ).execute()
        return len(payload)

    def upsert_contract(self, contract: MarketContract) -> None:
        self.client.table("market_contracts").upsert({
            "product": contract.product,
            "raw_contract_symbol": contract.raw_contract_symbol,
            "continuous_symbol": contract.continuous_symbol,
            "expiration": _iso(contract.expiration),
            "roll_date": _iso(contract.roll_date),
        }, on_conflict="product,raw_contract_symbol").execute()

    def upsert_rollover(self, rollover: ContractRollover) -> None:
        self.client.table("market_contract_rollovers").upsert({
            "product": rollover.product,
            "from_contract": rollover.from_contract,
            "to_contract": rollover.to_contract,
            "roll_date": _iso(rollover.roll_date),
            "provider": rollover.provider,
        }, on_conflict="product,from_contract,to_contract").execute()

    def upsert_session(self, session: MarketSession) -> None:
        self.upsert_contract(session.contract)
        contract = self.client.table("market_contracts").select("id").eq(
            "product", session.contract.product
        ).eq("raw_contract_symbol", session.contract.raw_contract_symbol).single().execute()
        contract_id = contract.data["id"]
        payload = asdict(session)
        payload.pop("contract")
        payload["session_date"] = _iso(session.session_date)
        payload["contract_id"] = contract_id
        self.client.table("market_sessions").upsert(payload, on_conflict="session_date").execute()

    def get_session(self, session_date: date) -> MarketSession | None:
        response = self.client.table("market_sessions").select(
            "*, market_contracts(*)"
        ).eq("session_date", _iso(session_date)).maybe_single().execute()
        if response is None or not response.data:
            return None
        row: dict[str, Any] = response.data
        contract_row = row.pop("market_contracts")
        row.pop("contract_id", None)
        row.pop("created_at", None)
        row["session_date"] = date.fromisoformat(row["session_date"])
        contract_row.pop("id", None)
        contract_row.pop("created_at", None)
        if contract_row.get("expiration"):
            contract_row["expiration"] = date.fromisoformat(contract_row["expiration"])
        if contract_row.get("roll_date"):
            contract_row["roll_date"] = date.fromisoformat(contract_row["roll_date"])
        row["contract"] = MarketContract(**contract_row)
        return MarketSession(**row)

    def get_bars(self, start: datetime, end: datetime, symbol: str | None = None) -> Sequence[MarketBar]:
        query = self.client.table("market_bars").select("*").gte(
            "timestamp", _iso(start)
        ).lt("timestamp", _iso(end)).order("timestamp")
        if symbol:
            query = query.eq("symbol", symbol)
        response = query.execute()
        return [MarketBar(
            symbol=row["symbol"],
            timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
            timeframe=row["timeframe"],
            open=float(row["open"]), high=float(row["high"]), low=float(row["low"]), close=float(row["close"]),
            volume=float(row["volume"]), provider=row["provider"],
            ingested_at=datetime.fromisoformat(row["ingested_at"].replace("Z", "+00:00")),
            available_at=datetime.fromisoformat(row["available_at"].replace("Z", "+00:00")),
        ) for row in (response.data or [])]
