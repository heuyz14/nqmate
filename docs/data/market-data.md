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

Full-session NQ/ES ingestion uses policy
`equity-full-session-expiry-exclusive-v2`: choose the nearest active contract
whose last trade date is strictly after the research date. The expiring
quarterly contract stops at 09:30 ET and cannot supply a complete RTH session.
The adapter uses metadata available on the requested date, not tomorrow's
contract lookup. Cached contracts are refreshed on expiration day.
See [CME NQ specifications](https://www.cmegroup.com/cn-t/markets/equities/nasdaq/e-mini-nasdaq-100.contractSpecs.html?videoId=6370880990112).

Raw expired-contract bars remain stored for provenance. Session-based feature,
analogue and strategy reads explicitly select the reconstructed session's raw
contract. Chart reads filter by the selected session contract where available.
No price splicing/back-adjustment is performed, and prior-contract gap inputs
remain absent. Recovery batches record the policy version in their JSON report.

NQ is contract-based. Implement `ContinuousContractResolver`; track product, active contract, expiration, and roll date. Preserve both `raw_contract_symbol` and `continuous_symbol`. Do not mix prices across rolls without adjustment.

## Bars and sessions

Start with minute bars; avoid every-tick storage. `market_bars` contains `id`, `symbol`, `timestamp`, `timeframe`, OHLC, `volume`, `provider`, and `ingested_at`, with uniqueness across `(symbol, timestamp, timeframe, provider)`. Build U.S. trading sessions from bars, including overnight open/high/low/close and regular-session OHLC. See [ARCHITECTURE.md](../ARCHITECTURE.md) for storage ownership.

The 1-minute series is the canonical historical input. The derived candle job persists deterministic 5-minute, 15-minute, 1-hour, 2-hour, 4-hour, and daily candles from stored minute bars rather than requesting duplicate provider series. The 2-hour and 4-hour candles represent the 120-minute and 240-minute horizons used by ML. The API also accepts `120m` and `240m` aliases when calculating or retrieving candles. Weekly analysis should include an explicitly defined opening gap for each trading week, using point-in-time bars and preserving the relevant raw contract.

When reading candles, the API uses persisted bars for the requested canonical timeframe and aggregates only `1min` bars for an unsupported alias or an unpopulated range. It never aggregates already-derived bars into another result.

## Required session fields

`MarketSession` includes session date, NQ OHLC, overnight OHLC, prior-day high/low/close, gap points/percent, overnight return/range, ATR(14), and optional regime ID. Detailed calculations are defined in [features.md](../ml/features.md).

## Ingestion jobs

V2 paired raw history uses `jobs/backfill_research_market.py --start YYYY-MM-DD
--end YYYY-MM-DD` (run as a Python module from the repository root). It emits
weekly JSON quality reports, preserves raw NQ/ES contract identity, and does not
write reconstructed sessions by default. Add `--reconstruct-nq-sessions` to
persist complete-coverage NQ sessions; prior-contract prices are excluded from
gap inputs. Incomplete but otherwise valid minutes remain raw
evidence; invalid batches are excluded from writes. Research eligibility still
requires exchange-schedule, rollover, and point-in-time validation.

Repository `get_bars` calls without a symbol return NQ-prefixed symbols only;
pass an explicit ES raw contract to read ES. The date-keyed `market_sessions`
table remains NQ-only. Migration 022 adds `market_supporting_sessions` for ES,
keyed by product/date, with neutral `regular_*` OHLC names and a product-matching
contract foreign key. RLS is enabled with no browser-role permissions; only the
server service role can read/write. These are shared market records, not user-owned.

`get_session(day)` and `get_previous_session(day)` still default to NQ. Explicit
`product="ES"` reads use the supporting table. The shared Python calculation
record retains its legacy `nq_*` constructor fields for compatibility; the ES
storage/API adapter exposes them as `regular_*`.

After applying `apps/api/migrations/022_supporting_market_sessions.sql`, rebuild
ES sessions from existing canonical minutes without provider downloads:

```sh
apps/api/.venv/bin/python -m jobs.reconstruct_es_sessions \
  var/log/research-backfill-2025-20260907.jsonl \
  var/log/research-expiry-recovery-2025-20260908.jsonl \
  var/log/research-backfill-2026-through-0908-20260909.jsonl
```

Run after the active raw backfill finishes (or rerun afterward to include later
batches). The command uses the latest attempt per ES date, reconstructs in date
order, rechecks minute quality, and isolates prior levels by raw contract.
New provider runs may use `--reconstruct-es-sessions` alongside
`--reconstruct-nq-sessions`. The currently running process retains its old flags.

Coverage certification is a separate, report-only step. Run
`python -m jobs.certify_market_sessions REPORT...` with saved JSONL attempts in
attempt order. It accepts an exception only when the missing-minute pattern
exactly matches its reviewed CME Equity Index closure or early-close schedule;
all other rows remain quarantined. It never changes raw bars, persisted sessions,
or training eligibility. The first 2025–2026 output is
`var/log/market-session-certification-through-2026-09-08.json` and is not a
point-in-time or rollover certification.

Point-in-time snapshot construction is defined in
`nqmate_api.market.snapshots`. It emits immutable records at 08:30, 09:00,
09:25, 09:30, 10:00, and 12:00 Eastern. Only closed one-minute bars strictly
before the snapshot timestamp and available by that timestamp are passed to the
feature function; empty inputs are omitted rather than imputed.
The supplied `market_feature_function` derives the existing deterministic NQ
technical feature family and computes 5-minute NQ-vs-ES relative strength from
bars visible at the same timestamp; nullable warm-up features remain null.
The population job records this contract as feature version
`market-features-v2.1`.

Migration `023_session_feature_snapshots.sql` adds server-only persistence for
these records. `SupabaseMlRepository.create_snapshot` uses insert semantics;
the composite uniqueness key rejects conflicting rewrites of the same snapshot.
Apply the migration before running a snapshot persistence job.

Migration `024_snapshot_availability_policy.sql` records whether a snapshot is
`strict` (provider availability proves it was known at the time) or
`event_time_reconstructed` (the bar is treated as available one minute after its
event timestamp for historical research). Reconstructed records never rewrite
raw bar availability and must not be described as live-captured data.

`GET /api/v1/market/nq/supporting-context?session_date=YYYY-MM-DD` returns NQ as
primary, ES as supporting, and completed-session return differences. Missing ES
stays null. These full-session values must not enter historical prediction-time
features; aligned point-in-time ES momentum remains part of the snapshot phase.

Rollback: stop ES writers first, export supporting rows if populated, then drop
`market_supporting_sessions` and `market_contracts_id_product_key`. NQ tables are
untouched. Do not drop a populated supporting table without retaining its data.

Historical contract lookups omit `type=single` before 2025-03-12 because Massive
did not populate that field before that date. See the provider's
[contract reference](https://massive.com/docs/rest/futures/contracts).

- Daily historical backfill.
- Resumable weekly backfill batches for long historical ranges.
- Latest minute bars.
- Contract rollover check.
- Session construction.
- Derived candle population for `5m`, `15m`, `1h`, `2h`, `4h`, and `1d` via `jobs/populate_market_timeframes.py`.

Free-tier development may run manually or by cron. Do not treat the free provider as zero-latency trading data.

## Point-in-time requirements

Every bar has an availability/ingestion timestamp sufficient to determine whether it was known at prediction time. Training and backtests may use only data with `available_at <= T`; reject future timestamps and duplicate bars. Preserve the provider and contract used for each prediction.
