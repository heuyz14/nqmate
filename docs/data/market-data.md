## When to read this file

Read for NQ/ES futures providers, contracts, bars, sessions, market fields, and historical ingestion. Pair with [features.md](../ml/features.md) for calculations.

# Market Data

## MVP provider

Use Massive Futures Basic at approximately $0/month for historical NQ and related futures data: all futures tickers, reference/history data, minute aggregates, two years of history, and a five-call/minute limit. It is not a true live feed, so V1 emphasizes historical research, backtesting, overnight analysis, daily premarket bias, and a later live-data adapter.

Create a swappable provider immediately:

```python
class MarketDataProvider(Protocol):
    async def get_bars(...)
    async def get_contract(...)
    async def get_market_status(...)
    async def get_latest_price(...)
```

Implement `MassiveMarketDataProvider` first. Later providers may include Massive realtime, Databento, IBKR, Tradovate, or CME without changing feature code.

## Contracts and rollover

NQ is contract-based. Implement `ContinuousContractResolver`; track product, active contract, expiration, and roll date. Preserve both `raw_contract_symbol` and `continuous_symbol`. Do not mix prices across rolls without adjustment.

## Bars and sessions

Start with minute bars; avoid every-tick storage. `market_bars` contains `id`, `symbol`, `timestamp`, `timeframe`, OHLC, `volume`, `provider`, and `ingested_at`, with uniqueness across `(symbol, timestamp, timeframe, provider)`. Build U.S. trading sessions from bars, including overnight open/high/low/close and regular-session OHLC. See [ARCHITECTURE.md](../ARCHITECTURE.md) for storage ownership.

## Required session fields

`MarketSession` includes session date, NQ OHLC, overnight OHLC, prior-day high/low/close, gap points/percent, overnight return/range, ATR(14), and optional regime ID. Detailed calculations are defined in [features.md](../ml/features.md).

## Ingestion jobs

- Daily historical backfill.
- Latest minute bars.
- Contract rollover check.
- Session construction.

Free-tier development may run manually or by cron. Do not treat the free provider as zero-latency trading data.

## Point-in-time requirements

Every bar has an availability/ingestion timestamp sufficient to determine whether it was known at prediction time. Training and backtests may use only data with `available_at <= T`; reject future timestamps and duplicate bars. Preserve the provider and contract used for each prediction.

