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

Load the release schedule, ingest official values, deduplicate, store scheduled and released times, and calculate the surprise after release. The dashboard must expose upcoming important events and, after release, actual/consensus/previous and NQ response.

## Economic event model

`EconomicEvent` stores ID, event type, scheduled/released timestamps, actual, consensus, previous, absolute and standardized surprise, growth/inflation/rates directions, NQ expected effect, NQ actual 5m/30m/2h, and 10Y response at 5m/30m. Taxonomy includes Fed events, CPI/PPI/PCE/NFP/jobless claims/GDP/PMI/ISM/retail sales, and other required releases.

Raw surprise is `actual - consensus`. Prefer `standardized_surprise = (actual - consensus) / historical_std_of_release_surprises` to compare releases.

## Point-in-time correctness

Use ALFRED vintages whenever historical revisions could leak future information. For any prediction timestamp T, use only the release value and consensus available by T; never use final revised data, a later release, or complete-session labels. Store `scheduled_at`, `released_at`, and availability metadata distinctly.

## Catalyst guardrail

High-impact releases reduce confidence. If an event is within 15 minutes, cap confidence at 0.55 and recommend `WAIT_FOR_RELEASE`; do not issue a high-confidence pre-event recommendation for FOMC, CPI, or NFP.

