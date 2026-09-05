## When to read this file

Read when building dashboard pages, visual information hierarchy, chart overlays, loading/empty/error states, or research UI.

# Frontend Dashboard

## Evaluation desk

The `/evaluation` page is the Phase 9 evaluation desk. It reads the bounded ML registry, champion/challenger comparison, confidence calibration, and prediction drift endpoints and presents model state, attached versus scored outcomes, calibration bins, drift status, and promotion evidence. It is read-only and must clearly distinguish historical evidence from an active model.

The `/dashboard` page is the primary completed-session market desk. It displays a 5-minute SVG candle view with PDH/PDL/ONH/ONL/overnight midpoint/VWAP overlays, deterministic session metrics, stored bias evidence, cached high-impact news, and stored 15m/4H/daily momentum read-through. It is explicitly historical and does not imply live market data or automated execution.

The page uses `NEXT_PUBLIC_API_BASE_URL` and falls back to `http://localhost:8000/api/v1` for local development. Loading, API error, no-outcome, no-snapshot, and no-model states are explicit. It must not display secrets or imply that an eligible challenger is active.

## Pages

- `/dashboard`: bias/confidence, NQ location, overnight structure, key levels, next catalyst, news risk, analogues, and a candlestick chart with PDH/PDL/ONH/ONL/VWAP.
- `/news`: headline, time, source, entities, NQ relevance, directional effect, surprise, explanation, and macro/Fed/semiconductor/mega-cap/geopolitical filters.
- `/calendar`: time, event, importance, consensus, previous, actual, surprise, NQ response.
- `/regime`: dimensions, 20 closest sessions, aggregate outcomes, strategy performance.
- `/strategies`: conditions, sample size, win rate, expectancy, best/worst regimes.
- `/journal`: manual entry/exit/direction/setup/reason/screenshot/result R/notes linked to session, bias, regime, strategy, and news.
- `/research`: structured questions answered from internal normalized data.
- `/models` (later): versions, walk-forward metrics, calibration, importance/SHAP, regime/month/event performance, drift, and champion/challenger comparison.

## Primary layout

The main trading screen prioritizes current NQ, bias/confidence, catalyst, chart/context, bull/bear cases, high-impact news, and historical analogues. Do not overload it with raw model internals; diagnostics belong on `/models`.

The initial `/regime` implementation is a focused historical-regime finder. It submits the six Phase 5 pre-session features and prediction timestamp to `POST /regimes/similar`, then presents ranked matches, aggregate outcome fields, and zero-centered historical move ranges. The “Load stored features” action uses `GET /market/nq/analogue-features` so the backend remains the source of deterministic feature calculations; manual values remain available for research and incomplete sessions. Move ranges are historical evidence, not forecasts; strategy-specific performance belongs to the later strategy-memory phase.

The initial `/strategies` implementation provides a structured strategy creation form, saved-strategy list, active state, rule detail, and outcome-backed performance metrics. It shows an explicit empty state when no strategies or completed outcomes exist; it does not invent performance.

## UX rules

Use responsive Next.js/React/Tailwind UI and accessible controls. Every data-driven view needs loading, empty, and error states. Bias display must include direction, confidence, evidence, counter-signals, important levels, upcoming risks, and invalidation. Conservative catalyst guardrails must be visible.
