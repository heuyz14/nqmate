## When to read this file

Always read this file at session start. It is the concise handoff for what exists, what is active, and what should happen next.

# Current State

## Current Phase

Phase 3 — Macro Pipeline (Phase 2 complete)

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
- Deterministic feature endpoint added at `/api/v1/market/nq/features` with 5m/15m/30m returns, EMA 9/20/50, VWAP, VWAP distance, range position, prior-level distances, and nullable NQ/ES relative strength.
- macOS daily market updater added at `jobs/ingest_market_daily.py`, scheduled by `ops/com.nqmate.market-daily.plist` for 4:05 PM America/New_York.
- Phase 2 news slice added: Marketaux and Fed RSS adapters, strict normalized article/event models, deterministic NQ relevance scoring, and provider/ID deduplication store.
- Phase 2 requirements expanded: Forex Factory calendar, official-release priority, adaptive polling, multi-axis classification, surprise semantics, logical cross-source deduplication, and pre-event risk awareness.
- Phase 2 persistence/API slice added: Supabase migration `003_news.sql`, server-side article/event repository, and `/api/v1/news` plus `/api/v1/news/high-impact` read endpoints.
- Phase 2 calendar/polling slice added: Forex Factory USD calendar normalization, configurable ET adaptive polling cadence, and environment flags for source enablement and relevance thresholds.
- Phase 2 news recency slice added: Marketaux uses publication date filters and API news reads default to a 14-day hot cache while retaining the full Supabase archive.
- Forex Factory CSV export support verified against the configured `nfs.faireconomy.media/ff_calendar_thisweek.csv` feed; date/time values are normalized from the configured `FOREX_FACTORY_TIMEZONE`.
- Phase 2 calendar persistence/API slice added: migration `004_economic_calendar.sql`, stable provider/time event identity, and `/api/v1/macro/calendar` retrieval.
- Phase 2 ingestion slice added: configured Marketaux, Federal Reserve RSS, and Forex Factory providers are orchestrated by `jobs/ingest_news.py`; baseline deterministic article classification is persisted as cached events.
- Phase 2 catalyst-awareness slice added: `/api/v1/macro/upcoming` returns the next HIGH-impact event, minutes until release, pre/post-release risk state, and economic surprise when available; pure surprise/risk logic is tested.
- Phase 2 clustering slice added: normalized news events receive a stable logical-event key for near-duplicate grouping, with canonical-source selection preferring official Fed/BLS/BEA reporting; migration `005_news_clustering.sql` adds the persisted key.
- Phase 2 optional NLP slice added: `GeminiNewsExtractor` is behind `NEWS_NLP_ENABLED`, validates structured output, and is wrapped in a provider/ID cache; deterministic classification remains the default.
- Gemini configuration verified: the key authenticates successfully, the initial retired model was replaced with provider-recommended `gemini-3.6-flash`, and an NLP-enabled ingestion smoke test persisted structured fields successfully.
- Phase 2 completion slice added: clusters persist canonical provider, contributing providers, event count, and availability span; `/api/v1/news/clusters` exposes them, with migration `006_news_event_clusters.sql`.
- Phase 3 foundation slice added: official `BLSProvider` and point-in-time `MacroObservation` preserve release, retrieval, and vintage timestamps without fabricating release availability.
- Phase 3 persistence slice added: migration `007_macro_observations.sql`, `SupabaseMacroRepository`, and `/api/v1/macro/observations` provide bounded official-observation storage and reads.

## In Progress

Phase 3 macro pipeline implementation is ready to begin.

## Next

1. Apply migration `007_macro_observations.sql` in Supabase and run a BLS persistence smoke test
2. Add BLS release-calendar mapping and official BEA/FRED/ALFRED adapters
3. Add economic-event surprise interpretation and post-release reaction storage

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

2026-09-02
