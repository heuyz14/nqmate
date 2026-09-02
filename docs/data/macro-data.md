## When to read this file

Read for official macro sources, releases, surprise calculations, economic-event storage, and vintage-aware backtesting.

# Macro Data

## Sources

- Federal Reserve RSS/pages: FOMC decisions, monetary policy releases, speeches, testimony, and press releases.
- FRED/ALFRED: funds rate, 2Y/10Y yields, yield spread, unemployment, CPI, PCE, financial conditions, credit spreads, and liquidity proxies.
- BLS Public Data API: CPI, PPI, unemployment, payroll-related series, and labor history.
- BEA API: GDP, PCE, national accounts, income, consumption, and international trade.

Avoid Trading Economics in V1. SEC company events are owned by [news-data.md](news-data.md).

## Pipeline

Load the release schedule from [news-data.md](news-data.md), ingest official values, deduplicate, store scheduled and released times, and calculate the surprise after release. The dashboard must expose upcoming important events and, after release, actual/consensus/previous and NQ response. Source priority is official BLS/Fed/BEA, then Forex Factory for schedule/forecast, then Marketaux for breaking context.

The initial Phase 3 adapter is `BLSProvider` for the official BLS Public Data API v2. Its `MacroObservation` keeps `released_at`, `retrieved_at`, and `vintage_date` separate; because the BLS series response does not itself provide a release timestamp, the adapter leaves `released_at` and `vintage_date` null rather than inventing them. Historical backtests must use an explicitly known release time or the retrieval timestamp as the conservative availability boundary.

`BLSReleaseCalendarProvider` parses the official [BLS iCalendar schedule](https://www.bls.gov/schedule/news_release/bls.ics) into `ScheduledRelease` records. The calendar supplies the authoritative scheduled timestamp; it is kept separate from the later series observation and actual release value. `BLS_RELEASE_CALENDAR_URL` is configurable because public-network Akamai policies may deny some callers.

`SupabaseMacroRepository` persists these observations in `macro_observations`, and `/api/v1/macro/observations` provides bounded retrieval. Migration `007_macro_observations.sql` must be applied before persistence is used.

`FREDProvider` retrieves official FRED series and accepts `realtime_start`/`realtime_end` for ALFRED-style vintage queries; the returned `realtime_start` is stored as `vintage_date`. `BEAProvider` retrieves a requested official dataset/table/line/period. Neither adapter invents release timestamps; release-calendar mapping remains a separate input.

Explicit BLS observation/release pairs can be linked with `link_release_timestamp`; the period is supplied by the caller and is never inferred from a title. Calendar events persist raw surprise (`actual - forecast`) when both values are available. Migration `008_macro_surprises.sql` adds the stored surprise field.

`interpret_surprise` applies event-specific deterministic semantics: hotter inflation or stronger labor data can be NQ-bearish through rates, while stronger growth releases use a growth-positive mapping with an explicit rate-context caveat. Unknown event types remain `UNKNOWN`; the LLM does not calculate or override these fields. Migration `009_macro_surprise_interpretation.sql` stores the direction and rationale.

Post-release reactions are stored as associations in `macro_reactions` by event, instrument, horizon, points, percentage, and observed timestamp. They are descriptive outcomes, not causal claims; migration `010_macro_reactions.sql` adds the table and `/api/v1/macro/events/{id}/reactions` reads it.

`reaction_from_prices` deterministically calculates points and percentage return from an explicitly selected pre-event base price and post-event observed price. It rejects a zero base and does not select future bars implicitly; the caller must enforce the event timestamp and horizon.

Run `jobs/ingest_macro.py --series-id SERIES --start-year YYYY --end-year YYYY --skip-calendar` to ingest BLS observations when the BLS calendar feed is unavailable. The normal job can ingest both the calendar and observations when the official calendar endpoint is reachable.

## Economic event model

`EconomicEvent` stores ID, event type, scheduled/released timestamps, actual, consensus, previous, absolute and standardized surprise, growth/inflation/rates directions, NQ expected effect, NQ actual 5m/30m/2h, and 10Y response at 5m/30m. Taxonomy includes Fed events, CPI/PPI/PCE/NFP/jobless claims/GDP/PMI/ISM/retail sales, and other required releases.

Raw surprise is `actual - consensus`. Prefer `standardized_surprise = (actual - consensus) / historical_std_of_release_surprises` to compare releases.

## Point-in-time correctness

Use ALFRED vintages whenever historical revisions could leak future information. For any prediction timestamp T, use only the release value and consensus available by T; never use final revised data, a later release, or complete-session labels. Store `scheduled_at`, `released_at`, and availability metadata distinctly.

## Catalyst guardrail

High-impact releases reduce confidence. If an event is within 15 minutes, cap confidence at 0.55 and recommend `WAIT_FOR_RELEASE`; do not issue a high-confidence pre-event recommendation for FOMC, CPI, or NFP.
