## When to read this file

Read when implementing or consuming the FastAPI REST contract. Pair with the relevant data/domain document for semantics and validation.

# API Endpoints

Base path: `/api/v1`.

| Area | Endpoints |
|---|---|
| Market | `GET /market/nq/session/current`, `/market/nq/bars`, `/market/nq/levels`, `/market/nq/weekly-gaps`, `/market/nq/features`, and `/market/nq/session/{date}` |
| News | `GET /news`, `/news/high-impact`, `/news/clusters`, `/news/{id}`; `POST /news/refresh` |
| Macro | `GET /macro/calendar`, `/macro/upcoming`, `/macro/observations`, `/macro/events/{id}`, `/macro/events/{id}/reactions` |
| Bias | `GET /bias/current`, `/bias/history`, `/bias/{id}`; `POST /bias/generate`, `/bias/{id}/explain` |
| Regimes | `GET /regimes/current`, `/regimes/{id}`; `POST /regimes/similar` |
| Strategies | `GET /strategies`; `POST /strategies`; `GET/PATCH /strategies/{id}`; `GET /strategies/{id}/performance` |
| Knowledge | `POST /knowledge/query`; `GET /knowledge/session/{date}`, `/knowledge/regimes`, `/knowledge/strategy-evidence` |
| Backtests | `POST /backtests`; `GET /backtests/{id}` |
| ML (later) | `GET /ml/models`, `/ml/models/{id}`, `/ml/predictions/current`, `/ml/predictions/history`, `/ml/features/current`, `/ml/features/importance`, `/ml/calibration`, `/ml/performance`; protected `POST /ml/train`, `/ml/backtest` |
| Health | `GET /health` returns 200 and exposes database/graph health in Phase 0 |

## Contracts and rules

Use Pydantic validation and versioned response schemas. The Phase 1 session endpoint must return OHLC, ONH, ONL, PDH, PDL, overnight return/range, ATR, and gap. Bias responses must retain evidence, counter-evidence, invalidation, catalyst risk, model, feature, and prompt versions. ML training endpoints are protected and unavailable to the public frontend. `POST /bias/generate` validates a normalized snapshot and persists an immutable rules-based prediction; `GET /bias/current` returns the newest stored prediction. LLM explanations consume supplied evidence only and do not replace deterministic fields.

News reads return normalized event records backed by `news_articles` and `news_events`. `/news/high-impact` filters by the configured NQ relevance threshold; publication/release availability remains part of the stored record.

`/news` and `/news/high-impact` default to the latest 14 days and accept optional `start`/`end` ISO datetimes. Older records remain queryable through explicit ranges.

`/macro/calendar` returns persisted scheduled economic events filtered by ISO datetime range, with optional HIGH-impact filtering and a bounded limit. `/macro/upcoming` returns the next persisted HIGH-impact event within 14 days, raw `actual - forecast` surprise when both values exist, minutes until release, and the documented pre-event risk state.

`/macro/observations` returns persisted official macro observations, optionally filtered by `series_id`, with a bounded limit.

`POST /regimes/similar` accepts a current session date, feature vector, prediction timestamp, metric, and top-K bound, then returns point-in-time eligible historical matches. Each match includes aggregated 30m/60m returns, observed min/max ranges, open-to-close return, ONH/ONL-first rates, trend-day rate, and analogue bull rate.

`GET /market/nq/analogue-features?session_date=YYYY-MM-DD` returns the deterministic pre-session feature vector used by analogue retrieval for a stored market session.

`GET /knowledge/regimes` accepts optional independent ontology filters (`overnight_direction`, `overnight_volatility`, `gap`, `location`, `yield_regime`, and `catalyst_regime`) plus a bounded limit, and returns graph-backed semantic sessions. It does not read raw candles.

`GET /knowledge/strategy-evidence` uses the same filters to traverse `Strategy-[:PERFORMS_WELL_IN]->MarketRegime` and returns bounded strategy statistics. It returns an empty list until Phase 7 strategy memory creates strategy records.

`POST /strategies` validates and stores structured strategy rules. `GET /strategies` returns saved strategies and accepts an optional `active` filter. `GET /strategies/{id}` reads one strategy, `PATCH /strategies/{id}` replaces its structured rules, and `DELETE /strategies/{id}` safely deactivates it without deleting history. Migration `014_strategies.sql` is applied; the current strategy count is 0.

`POST /bias/generate` also accepts optional `analogueBullRate`, `analogueAvg30mReturn`, `analogueAvg60mReturn`, and `analogueSampleSize` fields. These values enrich deterministic evidence and cases but do not alter the Phase 4 rules score or confidence calculation.

The same request may include an `analogue` object containing `sessionDate`, `features`, `predictionTime`, `topK`, and `metric`. The API retrieves eligible matches, uses their aggregate summary for the bias evidence, and includes the ranked `analogue_matches` in the response when matches are found.
