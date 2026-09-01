## When to read this file

Read this for system boundaries, data flow, technology choices, repository layout, and cross-cutting engineering rules. Read the linked domain document for implementation detail.

# Architecture

## System architecture

```text
raw market / news / macro sources
              ↓
        ingestion adapters
              ↓
PostgreSQL/Supabase + Neo4j/Graphiti
              ↓
 deterministic feature and event services
              ↓
 historical outcomes + similarity + graph features
              ↓
       ML probabilities
              ↓
 deterministic bias score
              ↓
       LLM explanation
              ↓
       Next.js dashboard
```

The dependency chain is [Data → clean session model → deterministic features → news/macro events → historical outcomes → regime similarity → knowledge graph → ML probabilities → LLM explanation](PROJECT.md#high-level-roadmap). The system remains useful at each stage.

## Frontend/backend separation

`apps/web` is a Next.js, React, TypeScript, Tailwind CSS frontend using Lightweight Charts and TanStack Query. `apps/api` is a Python 3.12+ FastAPI backend using Pydantic, SQLAlchemy, Alembic, `httpx`, and `asyncio`. The frontend communicates with the backend only; provider credentials and service keys stay server-side.

## Deterministic market engine

Python owns OHLC, returns, ranges, VWAP, ATR, levels, gaps, relative strength, volatility, event timing, strategy statistics, and session labels. The LLM never calculates values that deterministic code can calculate. See [market-data.md](data/market-data.md) and [features.md](ml/features.md).

## Ingestion and storage

Provider adapters ingest market bars, news, Fed RSS, macro releases, BLS/BEA/FRED state, and SEC events. Normalize data before retrieval. PostgreSQL/Supabase stores bars, sessions, snapshots, events, predictions, strategies, setups, outcomes, trades, and version metadata. Neo4j AuraDB stores semantic and temporal relationships; Graphiti may provide temporal graph memory. Do not copy raw candles into the graph.

The minimum relational model includes `market_contracts`, `market_bars`, `market_sessions`, `market_snapshots`, `news_articles`, `news_events`, `news_entities`, `economic_events`, `economic_releases`, `strategies`, `strategy_rules`, `setup_occurrences`, `bias_predictions`, `prediction_evidence`, `prediction_outcomes`, `trades`, `trade_notes`, `model_versions`, and `feature_versions`.

## Retrieval and reasoning

Structured nearest neighbors retrieve up to 20 similar sessions. Graph queries retrieve regime/strategy/event relationships, then materialize reproducible numeric graph features for ML. The bias engine combines deterministic scoring, retrieval, and ML probabilities. The LLM receives evidence only and returns strict structured JSON containing direction, confidence, summary, bull case, bear case, invalidation, and risks.

## Provider abstractions

Define `MarketDataProvider` immediately and keep Massive swappable with future real-time, Databento, IBKR, Tradovate, or CME providers. Define `LLMProvider` so Gemini, OpenAI, Anthropic, or Ollama can be exchanged. Third-party APIs feed normalized internal services; narrow internal tools expose normalized data rather than arbitrary database access.

## Technology stack

Frontend: Next.js, React, TypeScript, Tailwind CSS, Lightweight Charts, TanStack Query. Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic. Data: PostgreSQL/Supabase, Neo4j AuraDB, optional pgvector. Science: Polars, pandas, NumPy, scikit-learn, XGBoost or LightGBM. NLP: Gemini structured output, optional sentence-transformers and FinBERT. Jobs start with APScheduler or cron; do not begin with Kafka, Celery, Temporal, or Kubernetes.

## Repository structure

```text
nq-bias/
├── apps/web/             # Next.js frontend
├── apps/api/             # FastAPI application
├── services/             # ingestion, features, NLP, bias, backtest, graph
├── packages/             # shared types, market models, config
├── jobs/                 # scheduled ingestion/build/evaluation jobs
├── models/               # regime and direction model artifacts/code
├── notebooks/
├── tests/                # unit, integration, backtest
├── docker-compose.yml
├── .env.example
├── README.md
└── pyproject.toml
```

## Engineering principles

- Prefer simple, maintainable architecture and incremental delivery.
- Keep the durable value in normalized datasets and versioned evidence.
- Make predictions immutable and reconstructable; store provider, feature, model, prompt, and dataset versions.
- Enforce `available_at <= prediction_time`; use ALFRED vintages where revisions could leak future information.
- Use RLS and never expose service keys; treat uploaded/external content as untrusted.
- Do not add paid services or future-phase complexity before explicitly requested.

## Scheduling and cost posture

Start with manual runs or cron/APScheduler. The intended ET schedule is 05:50 overnight features; hourly/news checkpoints from 06:00 through 15:30; pre-event and open bias around 08:25/09:25; and session evaluation at 16:15. The V1 target is $0/month using free Massive, Marketaux, Fed, FRED, BLS, BEA, SEC, Gemini, Supabase, Neo4j AuraDB, and Graphiti OSS tiers. When upgrading, improve real-time market data first, then news, macro, LLM capacity, and infrastructure.

Prompts live in source control and every prediction stores its prompt version. Logs must capture prediction ID, data timestamp, providers, news/macro counts, similar sessions, model, prompt version, runtime, and errors so an incorrect prediction can be reconstructed.
