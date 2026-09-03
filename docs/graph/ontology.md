## When to read this file

Read when creating Neo4j labels, relationships, graph synchronization, graph-backed queries, or graph-derived features.

# Knowledge Graph Ontology

## Ownership

Neo4j is semantic relationship memory, not numerical truth. PostgreSQL/Supabase remains the source for raw bars, numerical features, releases, predictions, and outcomes. Do not duplicate raw candles in Neo4j. [knowledge-memory.md](knowledge-memory.md) defines temporal memory and retrieval use.

The Python graph boundary in `apps/api/src/nqmate_api/graph/` owns constraint creation and idempotent semantic synchronization. Callers provide explicit regime dimensions; the graph layer does not infer undocumented classification thresholds.

The Phase 6 v0 classifier is in `apps/api/src/nqmate_api/graph/regimes.py`. Its explicit thresholds are: overnight return strong at `±0.005` and ordinary direction by sign; gap is flat within `±0.001` percent; overnight-range/ATR ratios classify below `1.0` as LOW, below `2.0` as NORMAL, below `3.0` as HIGH, and otherwise EXTREME. Location is based on the overnight range versus PDH/PDL. Yield change uses the same `±0.001` flat threshold. Missing yield data maps to `YIELDS_FLAT`; missing catalyst data maps to `NO_MAJOR_EVENT`. These are versioned v0 defaults, not learned claims.

## Nodes

`Asset`, `Company`, `Sector`, `MarketSession`, `MarketRegime`, `NewsEvent`, `MacroEvent`, `Indicator`, `Setup`, `Strategy`, `Prediction`, `Outcome`, and `Narrative`.

## Relationships

```text
NewsEvent -[:IMPACTS]-> Asset
NewsEvent -[:MENTIONS]-> Company
Company -[:BELONGS_TO]-> Sector
Sector -[:IMPACTS]-> Asset
MacroEvent -[:OCCURRED_DURING]-> MarketSession
MarketSession -[:CLASSIFIED_AS]-> MarketRegime
Setup -[:OCCURRED_DURING]-> MarketSession
Setup -[:CONFIRMED_BY]-> Indicator
Strategy -[:USES]-> Setup
Strategy -[:PERFORMS_WELL_IN]-> MarketRegime
Prediction -[:MADE_DURING]-> MarketSession
Prediction -[:SUPPORTED_BY]-> NewsEvent|Indicator
Prediction -[:RESULTED_IN]-> Outcome
MarketSession -[:SIMILAR_TO]-> MarketSession
```

## Regime dimensions

Keep separately queryable: overnight direction (`STRONG_UP`, `UP`, `FLAT`, `DOWN`, `STRONG_DOWN`), overnight volatility (`LOW`, `NORMAL`, `HIGH`, `EXTREME`), gap (`GAP_UP`, `FLAT_OPEN`, `GAP_DOWN`), location (`ABOVE_PRIOR_RANGE`, `INSIDE_PRIOR_RANGE`, `BELOW_PRIOR_RANGE`), yield regime (`YIELDS_UP`, `YIELDS_FLAT`, `YIELDS_DOWN`), and catalyst regime (`NO_MAJOR_EVENT`, `PRE_EVENT`, `POST_EVENT`, `MULTIPLE_HIGH_IMPACT_EVENTS`). Do not collapse them into one giant category.

## Synchronization acceptance

Sync sessions, regimes, events, strategies, setups, and outcomes. A graph-backed query must answer which strategies perform best in a high-volatility gap-up session with rising yields and return evidence.
