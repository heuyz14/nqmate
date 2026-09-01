## When to read this file

Always read this file at session start. It is the concise handoff for what exists, what is active, and what should happen next.

# Current State

## Current Phase

Phase 1 — Historical Market Engine (ready to start)

## Completed

- Documentation architecture created.
- Phase 0 repository skeleton created.
- Python 3.12 virtual environment and API dependencies installed.
- Next.js dependencies installed and production build verified.
- Git `origin` configured for `git@github.com:heuyz14/nqmate.git`.
- Hosted Supabase and Neo4j AuraDB connectivity verified through the API health endpoint.
- Phase 1 market domain slice: `MarketBar`, `MarketContract`, `MarketSession`, deterministic session calculations, ATR(14), contract selection, Massive response mapping, deduplication, and session API contract.
- Phase 1 persistence slice: Supabase migration and server-side repository payloads for contracts, minute bars, and sessions.

## In Progress

Phase 1 historical market engine implementation and persistence integration.

## Next

1. Apply `apps/api/migrations/001_market_engine.sql` in Supabase
2. Wire runtime ingestion and session reads to `SupabaseMarketRepository`
3. Add NQ contract metadata retrieval and rollover schedule handling
4. Run historical minute-bar ingestion/backfill
5. Validate session values against a trusted chart
6. Add chart-ready bar and level response data

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
