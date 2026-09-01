## When to read this file

Read to implement the historical NQ engine. Also read [market-data.md](../data/market-data.md), [features.md](../ml/features.md), and [endpoints.md](../api/endpoints.md).

# Goal

Ingest historical minute bars and produce correct NQ contract-aware sessions and deterministic market features.

# Dependencies

[Phase 0](phase-0-bootstrap.md), `MarketDataProvider`, Massive credentials, and storage connectivity.

# Tasks

- Implement `MassiveMarketDataProvider`, `ContinuousContractResolver`, market bar ingestion, deduplication, and rollover tracking.
- Build session segmentation and `MarketSession` persistence.
- Calculate PDH, PDL, PDC, ONH, ONL, midpoint, overnight return/range, opening gap, ATR(14), and initial technical features.
- Backfill 1–2 years where available in resumable weekly batches; expose `GET /market/nq/session/{date}` and chart-level data.
- Plan deterministic derived 1-hour, 4-hour, and daily candles from canonical minute bars, plus weekly opening-gap calculations.

# Acceptance Criteria

For any historical date the endpoint returns OHLC, ONH/ONL, PDH/PDL, overnight return/range, ATR, and gap; contract symbols and rolls are preserved; values are manually checked against a trusted chart.

# Tests

Unit-test every calculation, rollover, session boundary, duplicate-bar rejection, and point-in-time assertion; integration-test Massive ingestion and storage.

# Explicitly Out of Scope

News, macro, LLM bias, graph, ML, order flow without a suitable feed, and automated trading.

# Next Phase

[Phase 2 — News pipeline](phase-2-news.md).
