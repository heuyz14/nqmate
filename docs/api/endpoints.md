## When to read this file

Read when implementing or consuming the FastAPI REST contract. Pair with the relevant data/domain document for semantics and validation.

# API Endpoints

Base path: `/api/v1`.

| Area | Endpoints |
|---|---|
| Market | `GET /market/nq/session/current`, `/market/nq/bars`, `/market/nq/levels`, `/market/nq/weekly-gaps`, `/market/nq/features`, and `/market/nq/session/{date}` |
| News | `GET /news`, `/news/high-impact`, `/news/{id}`; `POST /news/refresh` |
| Macro | `GET /macro/calendar`, `/macro/upcoming`, `/macro/events/{id}` |
| Bias | `GET /bias/current`, `/bias/history`, `/bias/{id}`; `POST /bias/generate` |
| Regimes | `GET /regimes/current`, `/regimes/similar`, `/regimes/{id}` |
| Strategies | `GET /strategies`; `POST /strategies`; `GET/PATCH /strategies/{id}`; `GET /strategies/{id}/performance` |
| Knowledge | `POST /knowledge/query`; `GET /knowledge/session/{date}` |
| Backtests | `POST /backtests`; `GET /backtests/{id}` |
| ML (later) | `GET /ml/models`, `/ml/models/{id}`, `/ml/predictions/current`, `/ml/predictions/history`, `/ml/features/current`, `/ml/features/importance`, `/ml/calibration`, `/ml/performance`; protected `POST /ml/train`, `/ml/backtest` |
| Health | `GET /health` returns 200 and exposes database/graph health in Phase 0 |

## Contracts and rules

Use Pydantic validation and versioned response schemas. The Phase 1 session endpoint must return OHLC, ONH, ONL, PDH, PDL, overnight return/range, ATR, and gap. Bias responses must retain evidence, counter-evidence, invalidation, catalyst risk, model, feature, and prompt versions. ML training endpoints are protected and unavailable to the public frontend.

News reads return normalized event records backed by `news_articles` and `news_events`. `/news/high-impact` filters by the configured NQ relevance threshold; publication/release availability remains part of the stored record.
