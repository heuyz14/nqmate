# NQ Directional Bias AI — Free-Tier MVP System Specification

**Status:** Build-ready MVP specification  
**Target:** Personal NQ / Nasdaq-100 futures directional-bias research assistant  
**Primary constraint:** Start at approximately **$0/month** using free tiers and public data, while keeping provider interfaces swappable for future paid real-time feeds.  
**Last researched:** August 31, 2026

---

## 1. Product Vision

Build an AI-assisted market research application that produces a structured directional bias for Nasdaq-100 futures (NQ) before and during the U.S. trading session.

The system should combine:

- NQ price structure
- overnight market behavior
- cross-market context
- macroeconomic events
- breaking financial news
- NLP-based event interpretation
- technical indicators
- historical regime similarity
- saved trading strategies
- historical outcomes
- a temporal knowledge graph
- continuous statistical learning from completed sessions

The system is **decision support**, not an autonomous execution engine.

The assistant should never produce an unexplained `BUY` or `SELL` output. Every bias must include evidence, confidence, counter-evidence, important levels, upcoming catalysts, and explicit invalidation conditions.

Example output:

```text
NQ BIAS: MODERATELY BULLISH
Confidence: 67%

Primary drivers
- NQ above prior close and overnight midpoint
- NQ outperforming ES
- semiconductor news positive
- 10Y yield stable
- historical analogues favor continuation

Counter-signals
- overnight high has rejected twice
- CPI release in 35 minutes

Important levels
ONH: 24,820
ONL: 24,690
PDH: 24,845
PDL: 24,580
VWAP: 24,742

Bias invalidation
5-minute acceptance below 24,690 with rising 10Y yield.

Recommended state
Wait for confirmation. No prediction through CPI.
```

---

# 2. Core Design Principle

Separate the system into three layers.

## Layer A — Deterministic market engine

Python calculates:

- OHLC
- returns
- ranges
- VWAP
- ATR
- overnight levels
- prior-day levels
- gaps
- relative strength
- volatility
- event timing
- strategy statistics

The LLM does NOT calculate these when deterministic code can.

## Layer B — Retrieval and memory

Postgres and Neo4j store:

- sessions
- market features
- economic releases
- news events
- strategies
- setups
- predictions
- outcomes
- regime relationships

Historical similarity is computed using structured data and embeddings.

## Layer C — AI reasoning

The LLM:

- converts raw news to structured events
- explains macro implications
- generates bull and bear cases
- summarizes retrieved historical analogues
- produces a bias from supplied evidence
- explains uncertainty

The LLM is not the source of truth for market prices.

---

# 3. Free-Tier Data Stack

## 3.1 Futures Data — Massive Futures Basic

Use **Massive Futures Basic** for MVP historical NQ and related futures data.

Current free plan includes:

- $0/month
- all futures tickers
- 5 API calls/minute
- 2 years historical data
- CME / CBOT / NYMEX / COMEX
- reference data
- historical data
- minute aggregates

Important limitation:

**The free plan is NOT a true live futures feed.**

Therefore V1 should focus on:

1. historical feature engineering
2. backtesting
3. overnight analysis using available bars
4. daily premarket bias generation
5. manual/live-data adapter later

Create a provider abstraction immediately:

```python
class MarketDataProvider(Protocol):
    async def get_bars(...)
    async def get_contract(...)
    async def get_market_status(...)
    async def get_latest_price(...)
```

Implement:

```text
MassiveMarketDataProvider
```

Later add:

```text
MassiveRealtimeProvider
DatabentoProvider
IBKRProvider
TradovateProvider
CMEProvider
```

without changing feature-engine code.

Source:
https://massive.com/pricing?product=futures

---

## 3.2 Financial News — Marketaux Free

Use **Marketaux** instead of Benzinga for V1.

Free tier currently provides:

- $0/month
- 100 requests/day
- 3 articles per request
- global financial market news
- instant news access
- metadata
- entity tracking
- many global news sources

Use queries focused on:

- Nasdaq
- technology
- semiconductors
- AI
- mega-cap tech
- monetary policy
- inflation
- Treasury yields
- geopolitical shocks

Maintain a high-impact ticker universe:

```text
NVDA
MSFT
AAPL
AMZN
GOOGL
META
AVGO
TSLA
AMD
NFLX
```

Do NOT poll continuously.

Suggested free-tier polling:

```text
06:00 ET
07:00 ET
08:00 ET
08:25 ET
08:45 ET
09:15 ET
09:25 ET
10:00 ET
12:00 ET
14:00 ET
15:30 ET
```

Batch multiple symbols/categories into each request where supported.

Store all fetched stories so the application never pays/request-limits itself by repeatedly retrieving the same news.

Source:
https://www.marketaux.com/pricing

---

# 4. Free Macro Sources

Avoid Trading Economics in V1.

Use official public sources.

## Federal Reserve

Use Federal Reserve RSS feeds and pages for:

- FOMC announcements
- monetary-policy releases
- speeches
- testimony
- press releases

Feed page:

https://www.federalreserve.gov/feeds/feeds.htm

Pipeline:

```text
Fed RSS
   ↓
feed parser
   ↓
deduplication
   ↓
NLP event extractor
   ↓
MacroEvent
   ↓
Neo4j + Postgres
```

---

## FRED / ALFRED

Use for slower-changing macro state:

- federal funds rate
- 2Y / 10Y Treasury yields
- yield spread
- unemployment
- CPI history
- PCE
- financial conditions
- credit spreads
- liquidity proxies

Use ALFRED/vintage-aware data where backtests could otherwise leak future revisions.

Never train historical models using revised economic data that was unavailable at prediction time when vintage data is available.

Source:

https://fred.stlouisfed.org/docs/api/fred/

---

## BLS Public Data API

Use BLS for:

- CPI
- PPI
- unemployment
- payroll-related series
- labor-market history

Official public API supports JSON.

Source:

https://www.bls.gov/developers/

---

## BEA API

Use BEA for:

- GDP
- PCE
- national accounts
- income
- consumption
- international trade

Source:

https://apps.bea.gov/api/

---

## SEC EDGAR

Use SEC EDGAR for company-specific events.

Focus on major Nasdaq weights.

Useful documents:

```text
8-K
10-Q
10-K
```

V1 priority:

```text
8-K only
```

Process:

```text
new filing
→ identify company
→ extract filing sections
→ classify event
→ estimate NQ relevance
→ save structured event
```

---

# 5. Free AI / NLP

## Primary option: Gemini API free tier

Use Gemini free-tier models for:

- news extraction
- event classification
- summaries
- market-impact reasoning
- structured JSON output

Keep all model access behind:

```python
class LLMProvider(Protocol):
    async def extract_event(...)
    async def summarize(...)
    async def reason_bias(...)
```

Possible implementations:

```text
GeminiLLMProvider
OpenAILLMProvider
AnthropicLLMProvider
OllamaLLMProvider
```

This prevents provider lock-in.

Gemini currently has free-tier API access for selected models.

Source:

https://ai.google.dev/gemini-api/docs/pricing

### Privacy note

Free API tiers may permit provider use of submitted content for product improvement.

Do not send:

- brokerage credentials
- account IDs
- personal financial information
- secret API keys

---

# 6. Optional Fully Local AI

Add Ollama support later.

Suitable use cases:

- embeddings
- sentiment
- headline classification
- experiment/offline operation

Architecture:

```text
LLM_PROVIDER=gemini
```

or:

```text
LLM_PROVIDER=ollama
```

Do not make local LLM performance a blocker for V1.

---

# 7. Storage

## 7.1 Supabase Free / PostgreSQL

Primary relational/time-series data store.

Free tier is adequate for an MVP.

Store:

- market bars
- daily sessions
- feature snapshots
- news metadata
- macro events
- AI predictions
- strategy definitions
- setup occurrences
- outcomes
- user annotations

Avoid storing every tick in Supabase.

Start with minute bars.

---

## 7.2 Neo4j AuraDB Free

Use Neo4j for the knowledge graph.

V1 graph purposes:

- connect events to affected assets
- connect regimes to strategy performance
- connect sessions to similar sessions
- connect setups to indicators
- connect outcomes to setups
- represent evolving relationships

Do not duplicate all raw bars into Neo4j.

Postgres = numerical time-series truth.

Neo4j = semantic relationship memory.

---

## 7.3 Graphiti

Graphiti is Apache-2.0 licensed and can be used for temporal graph memory.

Use it for knowledge that changes over time.

Example:

```text
FedRegime
  hawkish: Jan 2026 → Apr 2026
  neutral: Apr 2026 → Jul 2026
  dovish: Jul 2026 → ...
```

Do not use Graphiti for raw candle ingestion.

---

# 8. Repository Architecture

Recommended monorepo:

```text
nq-bias/
│
├── apps/
│   ├── web/
│   │   └── Next.js frontend
│   │
│   └── api/
│       └── FastAPI application
│
├── services/
│   ├── ingestion/
│   ├── features/
│   ├── nlp/
│   ├── bias/
│   ├── backtest/
│   └── graph/
│
├── packages/
│   ├── shared-types/
│   ├── market-models/
│   └── config/
│
├── jobs/
│   ├── ingest_market.py
│   ├── ingest_news.py
│   ├── ingest_macro.py
│   ├── build_session.py
│   └── evaluate_predictions.py
│
├── models/
│   ├── regime/
│   └── direction/
│
├── notebooks/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── backtest/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── pyproject.toml
```

---

# 9. Recommended Technology Stack

## Frontend

```text
Next.js
React
TypeScript
Tailwind CSS
Lightweight Charts
TanStack Query
```

## Backend

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
Alembic
httpx
asyncio
```

## Data

```text
PostgreSQL / Supabase
Neo4j AuraDB
pgvector optional
```

## Data science

```text
Polars
pandas
NumPy
scikit-learn
XGBoost or LightGBM later
```

## NLP

```text
Gemini API
Pydantic structured output
sentence-transformers optional
FinBERT optional
```

## Jobs

Start simple:

```text
APScheduler / cron
```

Do NOT begin with Kafka, Celery, Temporal, or Kubernetes.

Introduce infrastructure only after the MVP requires it.

---

# 10. Core Domain Model

## MarketSession

```python
MarketSession:
    id: UUID
    session_date: date

    nq_open: float
    nq_high: float
    nq_low: float
    nq_close: float

    overnight_open: float
    overnight_high: float
    overnight_low: float
    overnight_close: float

    prior_day_high: float
    prior_day_low: float
    prior_day_close: float

    gap_points: float
    gap_pct: float

    overnight_return: float
    overnight_range: float

    atr_14: float

    regime_id: UUID | None
```

---

# 11. Market Feature Schema

Create one feature snapshot for important times.

Examples:

```text
08:00
08:30
09:00
09:25
09:35
10:00
12:00
14:00
15:30
```

Schema:

```python
MarketSnapshot:
    timestamp
    nq_price

    distance_from_pdh
    distance_from_pdl
    distance_from_onh
    distance_from_onl
    distance_from_vwap

    overnight_return
    overnight_range_pct

    gap_pct

    atr_normalized_move

    es_return
    nq_es_relative_strength

    yield_10y_change
    yield_2y_change

    vix_change
    dxy_change

    breadth_score

    upcoming_event_minutes

    news_sentiment_score
    news_relevance_score
```

Not every free source will support every field immediately.

Store nullable features and progressively add providers.

---

# 12. Essential V1 Technical Features

Implement first:

```text
previous day high
previous day low
previous close

overnight high
overnight low
overnight midpoint
overnight range

overnight return

opening gap

5m return
15m return
30m return

ATR 14

EMA 9
EMA 20
EMA 50

VWAP

distance from VWAP

range position

relative NQ vs ES strength
```

Later:

```text
volume profile
value area
market profile
opening range
breadth
advance/decline
TICK
order flow
delta
DOM imbalance
```

Do not build order-flow features without a suitable real-time/tick feed.

---

# 13. News NLP Schema

Every article should be converted into a normalized event.

```json
{
  "event_type": "FED_SPEECH",
  "headline": "...",
  "published_at": "...",
  "source": "...",

  "entities": [
    "Federal Reserve",
    "NASDAQ"
  ],

  "topics": [
    "inflation",
    "interest_rates"
  ],

  "stance": "hawkish",

  "directional_impact": {
    "NQ": "bearish",
    "US10Y": "bullish",
    "USD": "bullish"
  },

  "impact_horizon": "intraday",

  "relevance": 0.91,
  "surprise": 0.62,
  "confidence": 0.81,

  "reason": "..."
}
```

Use strict enums.

---

# 14. Event Types

Initial taxonomy:

```text
FED_DECISION
FED_SPEECH
CPI
PPI
PCE
NFP
JOBLESS_CLAIMS
GDP
PMI
ISM
RETAIL_SALES

EARNINGS
GUIDANCE
AI_NEWS
SEMICONDUCTOR
REGULATION
M_AND_A
PRODUCT_LAUNCH
CYBERSECURITY

GEOPOLITICAL
ENERGY_SHOCK
CHINA_MACRO

TREASURY_YIELD_MOVE
DOLLAR_MOVE

OTHER
```

---

# 15. News Relevance Model

Do not treat all financial news equally.

Create:

```text
nq_relevance_score = 0..1
```

Inputs:

```text
source reliability
ticker/index relevance
Nasdaq weight
macro importance
novelty
surprise
recency
historical market sensitivity
```

Example weighting:

```python
score = (
    0.25 * entity_relevance
    + 0.20 * macro_importance
    + 0.20 * surprise
    + 0.15 * recency
    + 0.10 * source_quality
    + 0.10 * historical_sensitivity
)
```

This is a starting heuristic, not a permanent formula.

---

# 16. Economic Event Schema

```python
EconomicEvent:
    id
    event_type

    scheduled_at
    released_at

    actual
    consensus
    previous

    absolute_surprise
    standardized_surprise

    direction_for_growth
    direction_for_inflation
    direction_for_rates

    nq_expected_effect
    nq_actual_5m
    nq_actual_30m
    nq_actual_2h

    yield_10y_5m
    yield_10y_30m
```

---

# 17. Surprise Calculation

Raw surprise:

```text
actual - consensus
```

Better:

```text
standardized_surprise =
(actual - consensus) /
historical_std_of_release_surprises
```

This allows comparison between releases.

---

# 18. Knowledge Graph Ontology

## Nodes

```text
Asset
Company
Sector
MarketSession
MarketRegime
NewsEvent
MacroEvent
Indicator
Setup
Strategy
Prediction
Outcome
Narrative
```

## Core relationships

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

Prediction -[:SUPPORTED_BY]-> NewsEvent

Prediction -[:SUPPORTED_BY]-> Indicator

Prediction -[:RESULTED_IN]-> Outcome

MarketSession -[:SIMILAR_TO]-> MarketSession
```

---

# 19. Regime Representation

Create deterministic market-regime labels.

Dimensions:

## Overnight direction

```text
STRONG_UP
UP
FLAT
DOWN
STRONG_DOWN
```

## Overnight volatility

```text
LOW
NORMAL
HIGH
EXTREME
```

## Gap

```text
GAP_UP
FLAT_OPEN
GAP_DOWN
```

## Location

```text
ABOVE_PRIOR_RANGE
INSIDE_PRIOR_RANGE
BELOW_PRIOR_RANGE
```

## Yield regime

```text
YIELDS_UP
YIELDS_FLAT
YIELDS_DOWN
```

## Catalyst regime

```text
NO_MAJOR_EVENT
PRE_EVENT
POST_EVENT
MULTIPLE_HIGH_IMPACT_EVENTS
```

Combined representation:

```json
{
  "overnight_direction": "UP",
  "overnight_volatility": "NORMAL",
  "gap": "GAP_UP",
  "location": "ABOVE_PRIOR_RANGE",
  "yield_regime": "YIELDS_UP",
  "catalyst_regime": "PRE_EVENT"
}
```

Do not create one giant categorical string.

Keep dimensions separately queryable.

---

# 20. Strategy Representation

Users should be able to save strategies as structured objects.

```python
Strategy:
    id
    name
    description

    allowed_regimes
    required_conditions
    confirmation_conditions
    invalidation_conditions

    entry_logic
    target_logic
    stop_logic

    active
```

Example:

```json
{
  "name": "ONH Breakout Retest",
  "required_conditions": [
    "price_above_overnight_mid",
    "nq_relative_strength_positive"
  ],
  "trigger": [
    "break_above_onh",
    "retest_onh_holds"
  ],
  "invalidation": [
    "five_min_close_below_onh"
  ]
}
```

---

# 21. Session Outcome Schema

At session close calculate:

```text
open_to_close_return
high_after_open
low_after_open

morning_return
afternoon_return

maximum_upside_excursion
maximum_downside_excursion

ONH_broken?
ONL_broken?
PDH_broken?
PDL_broken?

first_break_direction

trend_day?
balanced_day?
reversal_day?
```

These labels fuel historical lookup.

---

# 22. Prediction Tracking

Every AI bias must be stored.

```python
BiasPrediction:
    id

    created_at
    session_date

    direction:
        STRONG_BEARISH
        BEARISH
        NEUTRAL
        BULLISH
        STRONG_BULLISH

    confidence

    bull_score
    bear_score

    catalyst_risk

    evidence_ids
    counter_evidence_ids

    invalidation_conditions

    model
    prompt_version
    feature_version
```

Never overwrite predictions.

Predictions are immutable records.

---

# 23. Define Prediction Targets

Avoid vague "was the AI correct?" evaluation.

Create measurable targets.

Examples:

## Target A

```text
NQ close > NQ price at prediction time
```

## Target B

```text
NQ 60-minute forward return > 0
```

## Target C

```text
first 1 ATR move after prediction was upward
```

## Target D

```text
10:00–12:00 return
```

Store multiple horizons.

```text
5m
15m
30m
60m
120m
close
```

---

# 24. Self-Learning Design

"Self-learning" should NOT mean letting the LLM modify itself.

Use four controlled mechanisms.

## A. Outcome recording

Automatically attach realized market outcomes to every prediction.

## B. Strategy statistics

Compute rolling:

```text
sample count
win rate
mean return
median return
expectancy
MFE
MAE
Sharpe-like ratio
confidence calibration
```

By:

```text
strategy
regime
event
time-of-day
direction
```

## C. Regime similarity

Find historical sessions similar to today.

## D. Weight recalibration

Train ML models periodically using accumulated structured data.

Do NOT allow live model updates during a trading session.

Retrain offline.

---

# 25. Historical Similarity Engine

V1 should use structured nearest neighbors.

Feature vector:

```text
overnight_return
overnight_range_pct
gap_pct
ATR percentile
NQ/ES relative strength
yield_change
distance_PDH
distance_PDL
distance_ONH
distance_ONL
macro_event_flag
news_score
```

Normalize features.

Use:

```text
StandardScaler
NearestNeighbors
cosine or euclidean distance
```

Return:

```text
top 20 similar sessions
```

Aggregate:

```text
next_30m_return
next_60m_return
open_to_close
ONH break rate
ONL break rate
trend-day probability
```

---

# 26. ML Model Roadmap

Do not begin with deep learning.

## Baseline

Logistic regression.

Target:

```text
60-minute return > 0
```

Benefits:

- interpretable
- easy calibration
- exposes leakage

## Model 2

XGBoost or LightGBM.

## Model 3

Regime-specific ensemble.

Potential:

```text
P(up) =
0.35 * logistic
+ 0.40 * XGBoost
+ 0.25 * historical_similarity
```

LLM should summarize these probabilities, not invent its own probability.

---

# 27. Prevent Look-Ahead Bias

Critical rule.

Every feature must have:

```text
available_at
```

At prediction time `T`, only use rows where:

```text
available_at <= T
```

Never use:

- final daily OHLC
- revised macro values not available then
- articles published later
- future indicator values
- complete-session labels

Backtest code should assert this condition.

---

# 28. Bias Engine

Bias generation consists of deterministic scoring + retrieval + LLM explanation.

## Step 1 — Build current snapshot

```text
market features
macro context
news context
upcoming events
```

## Step 2 — Retrieve analogues

```text
20 nearest sessions
```

## Step 3 — Retrieve strategy memory

Neo4j:

```text
strategies historically successful
in current regime
```

## Step 4 — ML probability

```text
P(up)
P(down)
```

## Step 5 — deterministic score

Example:

```text
market_structure   +0.30
cross_market       +0.15
news               +0.10
macro              -0.20
historical         +0.20
ML                 +0.18
-------------------------
raw score          +0.73
```

Normalize to `[-1, 1]`.

## Step 6 — LLM

LLM receives evidence only.

It outputs:

```json
{
  "direction": "BULLISH",
  "confidence": 0.67,
  "summary": "...",
  "bull_case": [],
  "bear_case": [],
  "invalidation": [],
  "upcoming_risks": []
}
```

---

# 29. Confidence Calibration

Do not let the LLM freely choose confidence forever.

Eventually calibrate.

For predictions marked 70% bullish:

```text
Did the chosen target actually finish bullish ~70%?
```

Generate bins:

```text
50-55
55-60
60-65
65-70
70-75
75-80
80+
```

Plot predicted vs observed accuracy.

Use:

```text
Brier score
log loss
calibration curve
```

---

# 30. Bias States

Keep output conservative.

```text
STRONG_BEARISH
BEARISH
SLIGHT_BEARISH
NEUTRAL
SLIGHT_BULLISH
BULLISH
STRONG_BULLISH
```

Require strong evidence for extremes.

Example:

```text
strong >= 0.75
bullish >= 0.40
slight >= 0.15
neutral -0.15..0.15
```

These thresholds should later be calibrated.

---

# 31. Catalyst Guardrail

Major macro releases should reduce confidence.

Example rule:

```python
if high_impact_event_within_15_minutes:
    confidence_cap = 0.55
    recommendation = "WAIT_FOR_RELEASE"
```

For FOMC / CPI / NFP:

```text
no high-confidence directional recommendation immediately before event
```

---

# 32. REST API Design

Base:

```text
/api/v1
```

## Market

```text
GET /market/nq/session/current
GET /market/nq/bars
GET /market/nq/levels
GET /market/nq/features
```

## News

```text
GET /news
GET /news/high-impact
POST /news/refresh
GET /news/{id}
```

## Macro

```text
GET /macro/calendar
GET /macro/upcoming
GET /macro/events/{id}
```

## Bias

```text
GET /bias/current
POST /bias/generate
GET /bias/history
GET /bias/{id}
```

## Regimes

```text
GET /regimes/current
GET /regimes/similar
GET /regimes/{id}
```

## Strategies

```text
GET /strategies
POST /strategies
GET /strategies/{id}
PATCH /strategies/{id}
GET /strategies/{id}/performance
```

## Knowledge

```text
POST /knowledge/query
GET /knowledge/session/{date}
```

## Backtests

```text
POST /backtests
GET /backtests/{id}
```

---

# 33. Agent Tools / MCP-Like Interface

Expose narrow internal tools instead of arbitrary database access.

```text
get_current_market_snapshot

get_overnight_structure

get_key_levels

get_upcoming_macro_events

get_relevant_news

get_similar_sessions

get_strategy_stats

get_regime

get_prediction_history
```

Later wrap these as an MCP server.

Important:

The MCP should access your **normalized internal data**.

Avoid making the LLM independently call every third-party API.

Preferred:

```text
third-party APIs
       ↓
ingestion
       ↓
your database
       ↓
your deterministic services
       ↓
MCP tools
       ↓
AI assistant
```

---

# 34. Frontend Pages

## `/dashboard`

Primary trader view.

Cards:

```text
Bias
Confidence
NQ location
Overnight structure
Key levels
Next catalyst
News risk
Historical analogues
```

Chart:

```text
NQ candles
PDH
PDL
ONH
ONL
VWAP
```

---

## `/news`

Show:

```text
headline
time
source
entities
NQ relevance
bullish/bearish effect
surprise
AI explanation
```

Filters:

```text
macro
Fed
semiconductors
mega-cap
geopolitics
```

---

## `/calendar`

Economic calendar.

Columns:

```text
time
event
importance
consensus
previous
actual
surprise
NQ response
```

---

## `/regime`

Current regime + historical matches.

Show:

```text
regime dimensions
20 closest sessions
aggregate outcomes
strategy performance
```

---

## `/strategies`

Create/edit saved strategies.

Show:

```text
conditions
sample size
win rate
expectancy
best regimes
worst regimes
```

---

## `/journal`

Record manual trades.

```text
entry
exit
direction
setup
reason
screenshot URL
result R
notes
```

Connect trades to:

```text
session
bias
regime
strategy
news
```

---

## `/research`

Ask:

```text
How does ONH breakout perform when NQ gaps up
but the 10Y yield is rising?
```

Agent performs structured query.

---

# 35. Suggested UI Layout

```text
┌──────────────────────────────────────────────────────┐
│ NQ 24,742    BIAS: BULLISH 67%    CPI 08:30         │
├────────────────────────────┬─────────────────────────┤
│                            │ Market Context          │
│      NQ CHART              │ ONH 24,820             │
│                            │ ONL 24,690             │
│                            │ PDH 24,845             │
│                            │ VWAP 24,735            │
├────────────────────────────┼─────────────────────────┤
│ Bull Case                  │ Bear Case               │
│ ...                        │ ...                     │
├────────────────────────────┴─────────────────────────┤
│ High Impact News                                     │
├──────────────────────────────────────────────────────┤
│ Historical Analogues                                 │
└──────────────────────────────────────────────────────┘
```

---

# 36. Database Tables

Minimum relational schema:

```text
market_contracts
market_bars
market_sessions
market_snapshots

news_articles
news_events
news_entities

economic_events
economic_releases

strategies
strategy_rules
setup_occurrences

bias_predictions
prediction_evidence
prediction_outcomes

trades
trade_notes

model_versions
feature_versions
```

---

# 37. `market_bars`

```sql
id
symbol
timestamp
timeframe
open
high
low
close
volume
provider
ingested_at
```

Unique index:

```text
(symbol, timestamp, timeframe, provider)
```

---

# 38. `news_events`

```text
id
article_id

event_type
event_timestamp

stance
nq_direction

relevance
surprise
confidence

summary
reason

model_version
created_at
```

---

# 39. `bias_predictions`

```text
id

timestamp
session_date

direction
confidence

score_market
score_macro
score_news
score_history
score_ml
total_score

bull_case_json
bear_case_json
invalidation_json

model_version
feature_version
prompt_version
```

---

# 40. Data Ingestion Jobs

## Market ingestion

```text
daily historical backfill
latest minute bars
contract rollover check
```

## News ingestion

```text
poll Marketaux
deduplicate URL / UUID
store article
queue NLP
```

## Fed ingestion

```text
poll RSS
deduplicate
run NLP
```

## Macro ingestion

```text
load release schedule
update actual after release
calculate surprise
```

---

# 41. Contract Rollover

NQ is contract-based.

Do not hardcode one ticker permanently.

Create:

```python
ContinuousContractResolver
```

Track:

```text
product = NQ
active_contract
expiration
roll_date
```

For analysis maintain both:

```text
raw_contract_symbol
continuous_symbol
```

Avoid mixing prices around roll without adjustment.

---

# 42. Background Schedule

Example ET schedule:

```text
05:50 build overnight features
06:00 fetch news
07:00 fetch news
08:00 build premarket snapshot
08:20 fetch macro/news
08:25 generate pre-event brief
08:45 refresh after 08:30 data
09:15 final premarket snapshot
09:25 generate open bias
09:35 post-open update
10:00 bias update
12:00 midday update
14:00 afternoon update
15:30 closing update
16:15 evaluate session
```

For free-tier development this can run manually or by cron.

---

# 43. MVP Bias Report

```markdown
# NQ Morning Brief — YYYY-MM-DD

## Bias

Direction:
Confidence:
Risk state:

## Overnight

Return:
Range:
Location:
ONH:
ONL:

## Prior session

PDH:
PDL:
PDC:

## Cross-market

ES relative strength:
10Y:
2Y:
DXY:
VIX:

## News

1.
2.
3.

## Macro calendar

Time | Event | Importance

## Historical matches

N:
Bullish:
Bearish:
Average 60m return:

## Bull case

...

## Bear case

...

## Invalidation

...

## No-trade condition

...
```

---

# 44. Development Phases

## Phase 0 — Project bootstrap

Deliverables:

```text
monorepo
Next.js app
FastAPI app
Supabase connection
Neo4j connection
Docker local dev
environment validation
```

Acceptance:

```text
GET /health -> 200
database health visible
graph health visible
```

---

## Phase 1 — Historical market engine

Build:

```text
Massive adapter
NQ contract resolver
market-bar ingestion
session segmentation
feature calculations
```

Backfill 1–2 years.

Acceptance:

For any historical date:

```text
GET /market/nq/session/{date}
```

returns:

```text
OHLC
ONH
ONL
PDH
PDL
overnight return
range
ATR
gap
```

---

## Phase 2 — News pipeline

Build:

```text
Marketaux adapter
Fed RSS adapter
deduplication
NLP extraction
relevance scoring
```

Acceptance:

A new article creates:

```text
NewsArticle
NewsEvent
entities
impact
confidence
```

---

## Phase 3 — Macro pipeline

Build:

```text
event taxonomy
Fed ingestion
BLS series
BEA series
FRED state features
economic-event storage
```

Acceptance:

Dashboard displays next important macro event.

---

## Phase 4 — Bias engine V0

No ML yet.

Create weighted deterministic score.

Example:

```text
overnight structure
gap
relative strength
technical location
macro risk
news score
```

Generate LLM explanation.

Acceptance:

Bias is reproducible from identical inputs.

---

## Phase 5 — Historical analogue engine

Backfill daily feature vectors.

Implement nearest neighbors.

Acceptance:

For today:

```text
GET /regimes/similar
```

returns 20 comparable historical sessions and outcomes.

---

## Phase 6 — Knowledge graph

Create Neo4j ontology.

Sync:

```text
sessions
regimes
events
strategies
setups
outcomes
```

Acceptance:

Query:

```text
Which strategies perform best in
high-volatility gap-up sessions with rising yields?
```

returns graph-backed evidence.

---

## Phase 7 — Strategy memory

Implement:

```text
strategy creation
rule representation
setup detection
strategy/session association
outcome statistics
```

Acceptance:

Each strategy has:

```text
n
win rate
expectancy
best regimes
worst regimes
```

---

## Phase 8 — ML baseline

Train:

```text
logistic regression
XGBoost
```

Use walk-forward validation.

Never random train/test split time-series data.

Acceptance:

Compare against:

```text
50% direction baseline
always-long baseline
simple overnight-direction baseline
```

---

## Phase 9 — Self-evaluation

Automatically score old predictions.

Build:

```text
calibration
accuracy by confidence
accuracy by regime
accuracy by event type
feature importance
```

---

# 45. Testing Strategy

## Unit

```text
overnight range
PDH/PDL
VWAP
gap
ATR
contract rollover
event surprise
bias score
```

## Integration

```text
Massive ingestion
Marketaux ingestion
Fed ingestion
Supabase writes
Neo4j sync
Gemini extraction
```

## Backtest tests

Assert:

```text
no future timestamps
no duplicate bars
no revised future data
prediction uses correct contract
```

---

# 46. ML Validation

Use walk-forward validation.

Example:

```text
Train:
months 1-6

Validate:
month 7

Train:
months 1-7

Validate:
month 8
```

Metrics:

```text
accuracy
precision
recall
ROC-AUC
Brier score
log loss

average return conditional on prediction
MFE
MAE
```

Accuracy alone is not enough.

---

# 47. Observability

Store logs for every bias generation.

```text
prediction_id
data_timestamp
market_provider
news_count
macro_count
similar_sessions
model
prompt_version
runtime_ms
errors
```

When an incorrect prediction occurs you need to reconstruct exactly what the assistant knew.

---

# 48. Prompt Versioning

Prompts live in source control.

Example:

```text
prompts/
  news_event_v1.md
  bias_reasoning_v1.md
  regime_summary_v1.md
```

Every prediction stores:

```text
prompt_version
```

Never silently modify production prompts.

---

# 49. AI Bias Prompt Contract

System should instruct:

```text
You are a market-research reasoning layer.

You may only use supplied evidence.

Do not invent prices, events, statistics, or historical outcomes.

Separate:
1. bullish evidence
2. bearish evidence
3. uncertainty
4. catalyst risk

If evidence conflicts, lower confidence.

Return strict JSON.
```

---

# 50. Security

Secrets:

```text
MASSIVE_API_KEY
MARKETAUX_API_KEY
FRED_API_KEY
GEMINI_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_KEY
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
```

Never expose service keys to the browser.

Frontend communicates only with backend.

---

# 51. Cost Control

Target V1:

| Component | Target cost |
|---|---:|
| Massive Futures Basic | $0 |
| Marketaux Free | $0 |
| Fed RSS | $0 |
| FRED | $0 |
| BLS | $0 |
| BEA | $0 |
| SEC | $0 |
| Gemini free tier | $0 |
| Supabase Free | $0 |
| Neo4j AuraDB Free | $0 |
| Graphiti OSS | $0 |
| Local development | $0 |
| **Target** | **$0/month** |

External provider limits and terms can change.

---

# 52. Known Free-MVP Limitations

The largest limitation is live NQ data.

The free Massive plan is excellent for:

```text
historical research
minute-bar backtests
feature development
regime modeling
```

but it should not be treated as a zero-latency trading feed.

Therefore V1 should be built as:

```text
research + premarket + delayed-data assistant
```

before becoming:

```text
real-time intraday assistant
```

---

# 53. Upgrade Path

When willing to spend money, first upgrade **market data**.

Priority:

```text
1. real-time NQ feed
2. better breaking-news feed
3. richer macro calendar
4. more LLM capacity
5. infrastructure
```

Do NOT pay for infrastructure before market-data quality.

Provider interfaces make each upgrade incremental.

---

# 54. Suggested First Paid Upgrade

Real-time futures feed.

Then application architecture remains:

```text
MarketDataProvider
        ↓
feature engine
        ↓
bias engine
```

Only provider changes.

---

# 55. First Build Sprint

Implement these exact tasks first.

```text
[ ] create monorepo
[ ] create apps/web
[ ] create apps/api

[ ] configure environment schema

[ ] connect Supabase
[ ] connect Neo4j

[ ] define MarketDataProvider

[ ] implement Massive provider

[ ] implement NQ contract resolver

[ ] ingest 30 historical trading days

[ ] implement MarketSession

[ ] calculate:
    [ ] PDH
    [ ] PDL
    [ ] PDC
    [ ] ONH
    [ ] ONL
    [ ] overnight midpoint
    [ ] overnight return
    [ ] overnight range
    [ ] gap
    [ ] ATR

[ ] expose GET /market/nq/session/{date}

[ ] create dashboard chart

[ ] overlay ONH / ONL / PDH / PDL

[ ] verify values against a trusted chart manually
```

Do not touch AI until these deterministic values are correct.

---

# 56. Second Sprint

```text
[ ] Marketaux adapter
[ ] Fed RSS adapter

[ ] news_articles table
[ ] news_events table

[ ] Gemini provider

[ ] news-event extraction schema

[ ] event taxonomy

[ ] NQ relevance score

[ ] dashboard news card
```

---

# 57. Third Sprint

```text
[ ] market snapshot model

[ ] deterministic bias scoring

[ ] generate bull case
[ ] generate bear case
[ ] generate invalidation
[ ] catalyst guardrail

[ ] store immutable prediction

[ ] bias-history page
```

---

# 58. Fourth Sprint

```text
[ ] historical feature matrix

[ ] StandardScaler

[ ] nearest-neighbor sessions

[ ] outcomes

[ ] analogue UI

[ ] feed analogue stats into bias engine
```

---

# 59. Fifth Sprint

```text
[ ] Neo4j ontology

[ ] graph synchronization

[ ] strategies

[ ] setup occurrences

[ ] strategy outcomes

[ ] graph-backed research questions
```

---

# 60. Sixth Sprint

```text
[ ] logistic baseline

[ ] walk-forward evaluation

[ ] XGBoost model

[ ] confidence calibration

[ ] prediction evaluation

[ ] model performance dashboard
```

---

# 61. V1 Definition of Done

V1 is complete when you can open the dashboard on a trading morning and see:

```text
current NQ context
overnight structure
key levels
important news
next macro event
market regime
20 similar historical sessions
historical directional statistics
saved-strategy relevance
AI bull case
AI bear case
directional bias
confidence
invalidation
```

and after the session:

```text
the prediction is automatically evaluated
session outcome is stored
strategy statistics update
historical memory becomes richer
```

---

# 62. What NOT to Build in V1

Avoid:

```text
automated trade execution
broker credentials
order routing
microsecond feeds
DOM prediction
reinforcement learning
online model retraining
deep neural networks
Kafka
Kubernetes
multiple autonomous agents debating each other
massive vector databases
fine-tuning an LLM
```

These add complexity without solving the core question:

> Does the system consistently create useful, evidence-backed NQ directional context?

---

# 63. Recommended Build Order

The correct dependency chain is:

```text
DATA
 ↓
CLEAN SESSION MODEL
 ↓
DETERMINISTIC FEATURES
 ↓
NEWS/MACRO EVENTS
 ↓
HISTORICAL OUTCOMES
 ↓
REGIME SIMILARITY
 ↓
KNOWLEDGE GRAPH
 ↓
ML PROBABILITY
 ↓
LLM EXPLANATION
```

Not:

```text
LLM
 ↓
random tools
 ↓
"bullish"
```

---

# 64. Main Engineering Principle

The project's durable value should live in your dataset.

After 500 trading sessions, the valuable asset should be:

```text
500 normalized NQ sessions
+ thousands of structured news events
+ macro surprises
+ regime labels
+ strategy occurrences
+ prediction histories
+ outcomes
+ temporal relationships
```

The AI model can then be replaced at any time.

That is what makes the assistant progressively more useful without depending on an LLM "remembering" everything.

---

# 65. External Sources Verified for This Specification

Checked August 31, 2026:

- Massive Futures pricing:
  https://massive.com/pricing?product=futures

- Marketaux pricing:
  https://www.marketaux.com/pricing

- Federal Reserve RSS:
  https://www.federalreserve.gov/feeds/feeds.htm

- FRED API:
  https://fred.stlouisfed.org/docs/api/fred/

- BLS API:
  https://www.bls.gov/developers/

- BEA API:
  https://apps.bea.gov/api/

- SEC APIs:
  https://www.sec.gov/search-filings/edgar-application-programming-interfaces

- Neo4j pricing:
  https://neo4j.com/pricing/

- Graphiti:
  https://github.com/getzep/graphiti

- Supabase pricing:
  https://supabase.com/pricing

- Gemini API pricing:
  https://ai.google.dev/gemini-api/docs/pricing

---



---

# 68. Advanced ML & Deep Learning Architecture

This section defines the post-MVP machine-learning roadmap. It extends the existing logistic-regression, XGBoost/LightGBM, historical-similarity, and calibration system.

The objective is **not** to replace deterministic market features or the knowledge graph. ML should consume those systems and estimate measurable market outcomes.

The progression should be:

```text
Deterministic Rules
        ↓
Logistic Regression
        ↓
XGBoost / LightGBM
        ↓
Multi-Target ML Ensemble
        ↓
NQ-Specific News Impact Model
        ↓
Temporal Deep Learning
        ↓
Multimodal Market Model
        ↓
Experimental Reinforcement Learning
```

Deep learning remains a post-V1 research stage. Do not delay the usable morning-bias product to build neural networks.

---

# 69. ML Feature Matrix

At each valid prediction timestamp create one immutable feature vector.

Example:

```python
features = {
    # Market structure
    "overnight_return": ...,
    "overnight_range_pct": ...,
    "gap_pct": ...,
    "range_position": ...,

    # Levels
    "distance_from_onh": ...,
    "distance_from_onl": ...,
    "distance_from_pdh": ...,
    "distance_from_pdl": ...,
    "distance_from_vwap": ...,

    # Momentum / volatility
    "return_5m": ...,
    "return_15m": ...,
    "return_30m": ...,
    "atr_percentile": ...,

    # Cross-market
    "es_return": ...,
    "nq_es_relative_strength": ...,
    "yield_10y_change": ...,
    "yield_2y_change": ...,
    "dxy_change": ...,
    "vix_change": ...,

    # News
    "news_relevance": ...,
    "news_surprise": ...,
    "news_direction_score": ...,
    "high_impact_news_count": ...,

    # Macro
    "minutes_until_macro_event": ...,
    "macro_event_importance": ...,
    "latest_macro_surprise": ...,

    # Retrieval / graph
    "analogue_bull_rate": ...,
    "analogue_avg_30m_return": ...,
    "analogue_avg_60m_return": ...,
    "best_strategy_expectancy": ...,
}
```

Every row must also contain:

```text
feature_timestamp
available_at
feature_version
session_date
contract
```

The training pipeline must reject features that were unavailable at prediction time.

---

# 70. Multi-Target Prediction System

Do not train only one generic `NQ up/down` model.

Train separate models for different questions.

## Direction models

```text
P(NQ higher in 5 minutes)
P(NQ higher in 15 minutes)
P(NQ higher in 30 minutes)
P(NQ higher in 60 minutes)
P(NQ higher in 120 minutes)
P(NQ higher at session close)
```

## Market-structure models

```text
P(ONH breaks before ONL)
P(ONL breaks before ONH)

P(PDH breaks)
P(PDL breaks)

P(opening range breakout succeeds)
P(opening range breakout fails)

P(trend day)
P(reversal day)
P(balanced day)
```

## Strategy models

```text
P(strategy reaches +1R before -1R)
P(strategy reaches target)
expected MFE
expected MAE
expected R
```

These outputs give the assistant a richer state than a single bullish/bearish probability.

Example:

```json
{
  "direction_30m_up": 0.54,
  "direction_60m_up": 0.67,
  "direction_close_up": 0.71,
  "onh_breaks_first": 0.74,
  "trend_day": 0.63
}
```

---

# 71. Baseline Model Suite

Before advanced models, train simple baselines.

Required:

```text
majority-class baseline
always-long baseline
overnight-direction baseline
logistic regression
```

Optional:

```text
random forest
```

Primary tabular model:

```text
LightGBM or XGBoost
```

A complex model is accepted only if it improves walk-forward out-of-sample performance over these baselines.

---

# 72. Gradient-Boosted Model Architecture

XGBoost/LightGBM should be the first serious production ML model.

Reasons:

- strong on tabular data
- handles nonlinear interactions
- works with moderate datasets
- fast training
- easier debugging than neural networks
- supports feature attribution
- supports missing values
- inexpensive inference

Suggested model groups:

```text
models/
  direction_30m/
  direction_60m/
  direction_close/
  onh_first/
  trend_day/
```

Each model directory should contain:

```text
model artifact
training configuration
feature list
training window
validation metrics
calibration model
version metadata
```

---

# 73. Feature Importance and SHAP

Use feature attribution to understand what the model is using.

For tree models, calculate:

```text
gain importance
permutation importance
SHAP values
```

Dashboard should support:

```text
Global importance
Today's prediction explanation
Importance by regime
Importance by model version
```

Example display:

```text
NQ/ES relative strength      +0.14 bullish
ON range position            +0.10 bullish
10Y yield change             -0.09 bearish
Gap size                     +0.06 bullish
News surprise                +0.04 bullish
VWAP distance                +0.03 bullish
```

SHAP is explanatory evidence, not proof of causality.

Track feature importance over time because market relationships can change.

---

# 74. ML Ensemble

Once multiple validated models exist, create an ensemble.

Example:

```text
Logistic probability
        │
XGBoost probability
        │
Historical analogue probability
        │
Regime-specific probability
        ↓
Meta ensemble
        ↓
Calibrated P(up)
```

Initial simple implementation:

```python
p_up = (
    0.20 * logistic_probability
    + 0.45 * xgboost_probability
    + 0.20 * analogue_probability
    + 0.15 * regime_probability
)
```

Do not permanently hardcode weights.

Later learn ensemble weights using validation data.

All component probabilities must be stored with the final prediction.

---

# 75. Regime-Specific Models

A single model may hide different market behaviors.

Potential specialized models:

```text
high-volatility model
low-volatility model
macro-event model
non-event model
gap-up model
gap-down model
overnight-trend model
range-bound model
```

Do not create regime-specific models until sample sizes are sufficient.

Use a minimum-sample threshold.

If insufficient:

```text
fall back to global model
```

---

# 76. NQ-Specific News Impact Model

Generic financial sentiment is not the final objective.

The system should learn:

> Given this news event and the market state at publication time, what historically happens to NQ afterward?

Training example:

```text
headline/article embedding
event type
entities
relevance
surprise
Fed stance
market regime
NQ location
NQ/ES relative strength
yield state
time of day
        ↓
targets
        ↓
NQ 5m return
NQ 15m return
NQ 30m return
NQ 60m return
```

This allows the system to distinguish:

```text
negative language
```

from:

```text
negative expected NQ impact
```

Those are not equivalent.

---

# 77. Automatic News Labels

When a news event arrives at timestamp `T`, store market reactions:

```text
NQ return T → T+5m
NQ return T → T+15m
NQ return T → T+30m
NQ return T → T+60m

ES return
10Y yield change
DXY change
VIX change
```

Example:

```text
08:14 article arrives

NQ 08:14 = X
NQ 08:19 = Y
NQ 08:44 = Z

reaction_5m  = Y / X - 1
reaction_30m = Z / X - 1
```

This gradually creates a proprietary NQ-news dataset.

Avoid claiming the article caused the move. Treat these values as post-event associations.

---

# 78. News Embeddings

Generate embeddings for:

```text
headline
summary
structured event description
```

Store embedding identifiers or vectors.

Uses:

```text
similar-news retrieval
clustering
novelty detection
historical impact lookup
ML input
```

Example query:

```text
Find the 30 historical news events most semantically
similar to this Fed headline and show NQ's subsequent reaction.
```

Combine semantic similarity with:

```text
event type
regime
time of day
asset relevance
```

Do not rely on embedding similarity alone.

---

# 79. Graph-Derived ML Features

The knowledge graph should generate numerical features for ML.

Examples:

```text
similar_regime_bull_rate
similar_regime_avg_60m_return

strategy_best_expectancy
strategy_best_sample_size

similar_news_avg_30m_return
similar_news_positive_rate

event_type_historical_impact

company_sector_weight_score

regime_strategy_match_score
```

Architecture:

```text
Neo4j / Graphiti
      ↓
graph queries
      ↓
numeric graph features
      ↓
feature store
      ↓
ML models
```

The ML model should never query Neo4j directly during training without a reproducible feature-generation step.

---

# 80. Temporal Sequence Dataset

Before deep learning, create a reusable sequence dataset.

For each prediction timestamp:

```text
last 30 minutes
last 60 minutes
last 120 minutes
```

Possible per-minute inputs:

```text
open
high
low
close
volume

return
range
body size
upper wick
lower wick

VWAP distance
EMA distance
ATR normalized range

ES return
yield change
VIX change
```

Normalize values relative to current price or rolling volatility where appropriate.

Store dataset-building code, not giant duplicated sequence blobs in the main database.

---

# 81. Deep Learning Stage 1 — LSTM / GRU

First sequence-model experiment:

```text
120 × minute feature matrix
        ↓
LSTM / GRU
        ↓
hidden representation
        ↓
dense classifier
        ↓
P(NQ higher in 60m)
```

Compare against XGBoost using exactly the same walk-forward periods.

Do not adopt the neural model unless it improves:

```text
Brier score
log loss
calibration
out-of-sample directional utility
```

A higher training accuracy is irrelevant.

---

# 82. Deep Learning Stage 2 — Temporal Transformer

Later experiment with a Transformer encoder.

Input:

```text
[t-119 ... t]
```

Each timestep contains:

```text
market features
cross-market features
time embeddings
event flags
```

Architecture concept:

```text
minute features
      ↓
linear projection
      ↓
time/session embeddings
      ↓
Transformer encoder
      ↓
pooled market embedding
      ↓
prediction heads
```

Prediction heads:

```text
30m direction
60m direction
close direction
ONH/ONL first
trend-day probability
```

This enables shared temporal representations across related targets.

---

# 83. Multi-Task Deep Learning

Instead of one neural network per target, a later model can share an encoder.

```text
                   Shared Market Encoder
                           │
        ┌──────────────────┼───────────────────┐
        ↓                  ↓                   ↓
   30m Direction      60m Direction       Trend Day
        │                  │                   │
        ↓                  ↓                   ↓
     Head A             Head B              Head C
```

Potential advantages:

- shared representation
- more efficient data usage
- related targets regularize one another

Only implement after single-target baselines are reliable.

---

# 84. Multimodal Market Model

Long-term research architecture:

```text
1-minute market sequence ──→ Temporal Encoder ─────┐
                                                   │
Engineered features ───────→ Feature Encoder ──────┤
                                                   │
News text ─────────────────→ Text Encoder ─────────┤
                                                   ├─→ Fusion Layer
Macro events ──────────────→ Macro Encoder ────────┤
                                                   │
Graph features ────────────→ Graph Encoder ────────┘
                                                        │
                                                        ↓
                                                Prediction Heads
```

Outputs:

```text
P(up 30m)
P(up 60m)
P(up close)

P(ONH first)
P(trend day)

expected return
expected volatility
```

This is an advanced research stage, not an MVP dependency.

---

# 85. Text Encoder Strategy

Do not train a language model from scratch.

Possible progression:

```text
V1:
LLM structured extraction

V2:
pretrained sentence embeddings

V3:
FinBERT / financial encoder embeddings

V4:
fine-tuned NQ news-impact encoder
```

The final classifier should combine text representation with contemporaneous market context.

The same headline can have different effects under different regimes.

---

# 86. Market Reaction as Context

News interpretation should compare expected reaction against observed reaction.

Example:

```text
hawkish Fed statement
expected:
    yields ↑
    NQ ↓

observed:
    yields ↑
    NQ ↑
```

Create features:

```text
expected_direction
actual_5m_direction
reaction_divergence
relative_strength_after_event
```

A failure to respond to bearish information may itself be informative.

The system should learn this statistically rather than encoding it permanently as a bullish rule.

---

# 87. Model Registry

Create a model registry table.

```text
ml_models

id
name
target
algorithm
version

trained_at
training_start
training_end

feature_version
dataset_version

validation_metrics_json
hyperparameters_json

artifact_path

active
```

Never replace a model artifact in place.

Every prediction references exact model versions.

---

# 88. Dataset Versioning

Training datasets must be reproducible.

Store:

```text
dataset_version
feature_version
label_version
start_date
end_date
symbols
bar_timeframe
data_provider
created_at
git_commit
```

If model performance changes, you must be able to reconstruct why.

---

# 89. Training Pipeline

Recommended command:

```bash
python -m models.train \
  --target direction_60m \
  --model xgboost \
  --dataset v3 \
  --walk-forward
```

Pipeline:

```text
load point-in-time data
        ↓
validate timestamps
        ↓
construct features
        ↓
construct labels
        ↓
walk-forward splits
        ↓
fit
        ↓
calibrate
        ↓
evaluate
        ↓
save artifact
        ↓
register model
```

---

# 90. Walk-Forward Evaluation for Multiple Horizons

Example:

```text
Train Jan–Jun
Validate Jul

Train Jan–Jul
Validate Aug

Train Jan–Aug
Validate Sep
```

Never shuffle time-series rows across train/test boundaries.

For intraday samples, avoid leakage from overlapping forward-return labels.

Consider:

```text
purging
embargo periods
```

when adjacent samples share future-return windows.

---

# 91. Model Calibration

Raw model probability is not automatically a trustworthy probability.

Test:

```text
Platt scaling
isotonic regression
```

Track:

```text
Brier score
expected calibration error
reliability curve
```

Example:

If predictions in the `0.70–0.75` bucket only finish bullish 55% of the time, confidence is overstated.

The dashboard should show calibrated probability.

---

# 92. Model Drift Detection

Financial relationships change.

Track rolling:

```text
feature distributions
prediction distributions
accuracy
Brier score
return conditional on prediction
SHAP distributions
```

Compare recent windows against training data.

Potential states:

```text
NORMAL
WATCH
DEGRADED
```

A degraded model should receive lower weight in the ensemble.

Do not automatically retrain merely because drift is detected.

---

# 93. Retraining Policy

Start with:

```text
monthly scheduled retraining
```

or:

```text
manual retraining after sufficient new data
```

Requirements before promotion:

```text
new model beats current model out-of-sample
calibration does not degrade materially
no leakage tests fail
performance improvement exists across multiple windows
```

Never update model weights live during a trading session.

---

# 94. Champion / Challenger Models

Maintain:

```text
Champion = current production model
Challenger = newly trained candidate
```

Run both on live snapshots.

Store both predictions.

Only promote challenger after sufficient forward observations.

This reduces the risk of replacing a working model because of one favorable backtest.

---

# 95. ML API Endpoints

Add later:

```text
GET /ml/models
GET /ml/models/{id}

GET /ml/predictions/current
GET /ml/predictions/history

GET /ml/features/current
GET /ml/features/importance

GET /ml/calibration
GET /ml/performance

POST /ml/train
POST /ml/backtest
```

Training endpoints should be protected and unavailable from the public frontend.

---

# 96. ML Prediction Schema

```python
MLPrediction:
    id
    created_at
    feature_timestamp

    model_id
    model_version
    feature_version

    target
    horizon

    raw_probability
    calibrated_probability

    predicted_class

    top_positive_features
    top_negative_features

    available_at
```

Bias predictions should reference one or more `MLPrediction` records.

---

# 97. Dashboard ML Panel

Add a compact panel:

```text
MODEL OUTLOOK

30m ↑        54%
60m ↑        67%
Close ↑      71%

ONH first    74%
Trend day    63%

Model confidence:
MODERATE

Strongest bullish factors:
+ NQ/ES relative strength
+ overnight location
+ analogue performance

Strongest bearish factors:
- rising 10Y
- macro event risk
```

Do not overload the primary trading screen with raw model internals.

Detailed diagnostics belong on `/models`.

---

# 98. `/models` Research Page

Include:

```text
active model versions
walk-forward metrics
calibration curves
feature importance
SHAP explanations
performance by regime
performance by month
performance by event type
prediction history
drift indicators
champion/challenger comparison
```

This page is for research, not trade execution.

---

# 99. Deep Learning Data Requirements

Do not interpret row count as independent sample count.

Two years of daily sessions gives only roughly hundreds of daily observations.

Minute data provides far more rows but observations are highly correlated.

Before serious deep learning, target:

```text
multiple years of minute data
clean contract-roll handling
stable feature definitions
point-in-time news
point-in-time macro data
walk-forward infrastructure
```

If those are unavailable, boosted trees are likely the better engineering choice.

---

# 100. Reinforcement Learning — Experimental Only

Reinforcement learning should be the final experimental stage.

Do NOT use RL to directly control a brokerage account.

Potential research environment:

```text
state:
    market features
    model probabilities
    regime
    news state

actions:
    LONG
    SHORT
    FLAT

reward:
    risk-adjusted simulated return
```

Problems to address:

```text
transaction costs
slippage
non-stationarity
reward hacking
overfitting
market-impact assumptions
survivorship bias
look-ahead bias
```

RL results must be evaluated in simulation and forward paper testing.

It is not part of V1.

---

# 101. Revised Intelligence Architecture

Long-term architecture:

```text
                         RAW SOURCES
                              │
            ┌─────────────────┼──────────────────┐
            ↓                 ↓                  ↓
       Market Data          News              Macro
            │                 │                  │
            ↓                 ↓                  ↓
    Deterministic       NLP Extraction      Event Engine
    Feature Engine            │                  │
            │                 └────────┬─────────┘
            │                          │
            ├──────────────┐           │
            ↓              ↓           ↓
       PostgreSQL     Knowledge Graph / Graphiti
            │              │
            │              ↓
            │        Graph Features
            │              │
            ├──────────────┤
            ↓              ↓
      Historical       Similarity
       Dataset           Engine
            │              │
            └───────┬──────┘
                    ↓
              ML ENSEMBLE
                    │
       ┌────────────┼─────────────┐
       ↓            ↓             ↓
    30m P(up)    60m P(up)    Structure Models
       │            │             │
       └────────────┼─────────────┘
                    ↓
              BIAS ENGINE
                    │
                    ↓
               LLM REASONER
                    │
                    ↓
          EXPLAINABLE NQ BRIEF
```

The LLM remains the explanation and interaction layer.

The numerical models remain responsible for statistical probabilities.

---

# 102. Revised ML Build Phases

## ML Phase A — Baselines

```text
[ ] create point-in-time feature matrix
[ ] create 30m / 60m / close labels
[ ] majority baseline
[ ] always-long baseline
[ ] logistic regression
[ ] walk-forward evaluation
```

## ML Phase B — Boosted Trees

```text
[ ] XGBoost or LightGBM
[ ] hyperparameter search within training windows
[ ] calibration
[ ] SHAP
[ ] model registry
[ ] champion/challenger
```

## ML Phase C — Multi-Target Models

```text
[ ] ONH-first target
[ ] ONL-first target
[ ] trend-day target
[ ] opening-range target
[ ] strategy-success targets
[ ] ensemble probabilities
```

## ML Phase D — News Intelligence

```text
[ ] store post-news market reactions
[ ] generate text embeddings
[ ] similar-news retrieval
[ ] train NQ-specific news-impact model
[ ] combine news model with market context
```

## ML Phase E — Deep Learning Research

```text
[ ] sequence dataset
[ ] LSTM/GRU baseline
[ ] temporal Transformer
[ ] multi-task heads
[ ] compare against boosted trees
```

## ML Phase F — Multimodal Research

```text
[ ] market encoder
[ ] text encoder
[ ] macro encoder
[ ] graph features
[ ] fusion architecture
[ ] calibrated multi-target output
```

## ML Phase G — Experimental RL

```text
[ ] simulation environment
[ ] transaction-cost model
[ ] paper-only policy research
[ ] compare against supervised strategies
```

---

# 103. ML Definition of Success

Do not judge the project by whether an advanced model sounds impressive.

A new model is useful only if it improves the system out of sample.

Required questions:

```text
Does it beat simple baselines?

Does it improve Brier score?

Is it calibrated?

Does it work across multiple market regimes?

Does it remain useful after costs/slippage assumptions?

Does it degrade gracefully?

Can its prediction be reconstructed?

Does it add information beyond historical similarity?

Does it improve decision quality rather than merely accuracy?
```

The best production model may remain a relatively simple ensemble.

Complexity is justified only by measurable forward value.

---

# 104. Updated Long-Term Roadmap

```text
V0
Deterministic market dashboard

        ↓

V1
News + macro + rule-based bias

        ↓

V2
Historical regime retrieval

        ↓

V3
Knowledge graph + strategy memory

        ↓

V4
Logistic regression + XGBoost/LightGBM

        ↓

V5
Multi-target calibrated ensemble

        ↓

V6
NQ-specific news-impact ML

        ↓

V7
LSTM / Temporal Transformer research

        ↓

V8
Multimodal market model

        ↓

V9
Experimental reinforcement-learning research
```

The system should remain usable at every stage. Later ML stages enhance the existing product rather than requiring a rewrite.


# 66. Immediate Codex Starting Prompt

Use this after creating the repository:

```text
Read this entire project specification before making changes.

Implement Phase 0 and Phase 1 only.

Requirements:

1. Create a pnpm monorepo with:
   - apps/web using Next.js + TypeScript
   - apps/api using Python FastAPI

2. Create strongly typed environment configuration.

3. Implement database connectivity abstractions for:
   - Supabase PostgreSQL
   - Neo4j

4. Define a MarketDataProvider interface.

5. Implement a MassiveMarketDataProvider.

6. Add models for:
   - MarketBar
   - MarketContract
   - MarketSession

7. Implement NQ contract resolution.

8. Implement historical bar ingestion.

9. Implement deterministic calculations for:
   - previous-day high
   - previous-day low
   - previous close
   - overnight high
   - overnight low
   - overnight midpoint
   - overnight range
   - overnight return
   - opening gap
   - ATR(14)

10. Add:
    GET /api/v1/market/nq/session/{date}

11. Add unit tests for every market calculation.

12. Never calculate trading features with an LLM.

13. Do not implement news, AI bias, Graphiti, ML, or automated trading yet.

Before coding, produce:
- proposed file tree
- database schema
- implementation order

Then implement incrementally and run tests after each logical section.
```

---

# 67. Future Research Questions

Once enough data exists, the system should answer questions such as:

```text
What happens when NQ gaps above PDH but yields rise overnight?

How frequently does the ONH hold after a positive semiconductor catalyst?

Does NQ relative strength versus ES predict the first-hour direction?

How does CPI surprise direction interact with premarket positioning?

Which saved strategy has the best expectancy in today's regime?

When the AI has >70% confidence, is it actually calibrated near 70%?

Which news categories have historically produced the largest NQ response?

When bearish macro news fails to push NQ lower, what happens next?
```

These research capabilities should become the long-term center of the product.
