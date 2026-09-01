## When to read this file

Always read this file at session start. It is the concise handoff for what exists, what is active, and what should happen next.

# Current State

## Current Phase

Phase 1 — Historical Market Engine (implementation complete; validation pending)

## Completed

- Documentation architecture created.
- Phase 0 repository skeleton created.
- Python 3.12 virtual environment and API dependencies installed.
- Next.js dependencies installed and production build verified.
- Git `origin` configured for `git@github.com:heuyz14/nqmate.git`.
- Hosted Supabase and Neo4j AuraDB connectivity verified through the API health endpoint.
- Phase 1 market domain slice: `MarketBar`, `MarketContract`, `MarketSession`, deterministic session calculations, ATR(14), contract selection, Massive response mapping, deduplication, and session API contract.
- Phase 1 persistence slice: Supabase migration and server-side repository payloads for contracts, minute bars, and sessions.
- Session reads now use `SupabaseMarketRepository`; empty dates return HTTP 404 rather than an infrastructure error.
- Contract metadata lookup, bounded backfill command, and chart-ready bars/levels endpoints added.
- One historical NQ session (`2026-08-28`) ingested from Massive into Supabase and verified through the API.
- Contract rollover transition persistence added in migration `002_contract_rollovers.sql`; ingestion records raw-contract changes.
- Backfill is rate-limited to Massive’s five requests per minute; the job reuses contracts until expiration and is safe to resume by date range.
- Phase 1 derived market slice added: `/market/nq/bars` supports `1h`, `4h`, and `1d` deterministic aggregation from stored minute bars; weekly opening-gap calculation is available in the market calculation layer.
- Weekly opening gaps are available through `/api/v1/market/nq/weekly-gaps`.

## In Progress

Phase 1 historical market engine implementation, persistence, and ingestion integration.

## Next

1. Validate session values, derived timeframes, and rollover dates against a trusted chart
2. Prepare the Phase 2 handoff after validation

## Important Decisions

- Python owns deterministic market calculations.
- Next.js is primarily the frontend; FastAPI is the application/data/ML backend.
- PostgreSQL/Supabase stores numerical and relational truth; Neo4j stores semantic relationships, not raw candles.
- Start with minute bars.
- Market providers must be swappable.
- The LLM explains supplied evidence rather than inventing market statistics.
- No automated trade execution in V1.
- Prevent look-ahead bias with point-in-time data.
- Deep learning is post-V1; XGBoost/LightGBM is the first serious ML model after the baseline.

## Blockers

None.

## Last Updated

2026-09-01
