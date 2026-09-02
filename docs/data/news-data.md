## When to read this file

Read for Marketaux, Fed RSS, SEC news/event ingestion, NLP extraction, relevance scoring, and news point-in-time rules.

# News Data

## Sources and free-tier approach

Use Marketaux Free rather than Benzinga for V1: approximately $0/month, 100 requests/day, three articles/request, metadata, entity tracking, and global financial news. Query Nasdaq, technology, semiconductors, AI, mega-cap tech, monetary policy, inflation, Treasury yields, and geopolitical shocks. Maintain a high-impact universe: NVDA, MSFT, AAPL, AMZN, GOOGL, META, AVGO, TSLA, AMD, NFLX.

Also ingest Federal Reserve RSS/pages for decisions, policy releases, speeches, testimony, and press releases. Use SEC EDGAR, prioritizing 8-K filings for major Nasdaq weights; later include 10-Q and 10-K.

Forex Factory machine-readable calendar exports are the primary schedule/consensus source for USD economic events. The current CSV export URL is `https://nfs.faireconomy.media/ff_calendar_thisweek.csv`; keep it configurable and parse its `Title`, `Country`, `Date`, `Time`, `Impact`, `Forecast`, `Previous`, and `URL` columns. Normalize CPI/Core CPI, PPI, payrolls, unemployment, JOLTS, claims, ISM, confidence, GDP, retail sales, FOMC-related events, and Fed speakers with event, currency, impact (`LOW`/`MEDIUM`/`HIGH`), scheduled time, actual, forecast, previous, and `forex_factory` source. Prefer USD and HIGH-impact events. Forex Factory supplies schedule and expectations; official releases own authoritative actuals. Official source ownership and surprise semantics live in [macro-data.md](macro-data.md).

## Polling and storage

Do not poll continuously. Use configurable adaptive polling: overnight low frequency, premarket medium frequency, highest priority 08:00–10:30 ET, lower frequency midday, and higher frequency 14:00–16:00 ET. Suggested ET polls are 06:00, 07:00, 08:00, 08:25, 08:45, 09:15, 09:25, 10:00, 12:00, 14:00, and 15:30. Configure `NEWS_POLL_INTERVAL_ACTIVE`, `NEWS_POLL_INTERVAL_IDLE`, `FOREX_FACTORY_ENABLED`, `MARKETAUX_ENABLED`, and `NEWS_MIN_NQ_RELEVANCE`; respect Marketaux’s free-tier limits. Batch requests where supported. Deduplicate by URL/provider UUID, store all fetched stories, and queue NLP once; do not repeatedly fetch the same story.

Keep the full normalized archive in Supabase, but treat the most recent 14 days as the hot cache for dashboard retrieval. Marketaux polling must use `published_after` (and `published_before` when needed) so stale provider responses do not refill the hot window. API reads default to the 14-day window and allow explicit ranges for research.

## Normalized event

Each `NewsArticle` becomes a strict-enum `NewsEvent` with article ID, event type, subtype, event timestamp, stance/sentiment, NQ direction, relevance, impact, surprise, confidence, themes, summary, reason, model version, and creation time. Initial categories are INFLATION, EMPLOYMENT, FED, INTEREST_RATES, TREASURY, ECONOMIC_GROWTH, CONSUMER, EARNINGS, MEGA_CAP_TECH, SEMICONDUCTORS, AI, GEOPOLITICAL, REGULATION, BANKING_CREDIT, and OTHER.

## NQ relevance

Calculate `nq_relevance_score` in `[0,1]` from source reliability, ticker/index relevance, Nasdaq weight, macro importance, novelty, surprise, recency, and historical market sensitivity. The starting heuristic is entity relevance .25, macro importance .20, surprise .20, recency .15, source quality .10, historical sensitivity .10; it is not permanent. Do not equate semantic sentiment with expected NQ impact: classify both. A semantically positive release can still be bearish for NQ if it implies higher rates.

For scheduled releases, retain actual, forecast, and previous; calculate raw surprise as `actual - forecast` and preserve its event-specific interpretation. Official BLS/Fed/BEA values override aggregator facts. Deduplicate equivalent reports across sources using semantic similarity, event type, entities, publication-time proximity, numeric values, and source; prefer official sources for canonical facts.

Expose the next HIGH-impact event and minutes until release. Use `EVENT_RISK` at T-30 minutes, `CRITICAL_EVENT_RISK` at T-5 minutes, process the release at T+0, and track initial reaction at T+1–5 and continuation/reversal at T+5–30 minutes. The bias layer must reduce confidence near critical catalysts.

## NLP and news ML

Hide model access behind `LLMProvider` (`extract_event`, `summarize`, `reason_bias`) and support Gemini first, with OpenAI, Anthropic, and Ollama adapters later. Store embeddings for headlines/summaries/structured descriptions when introduced. Record post-event NQ/ES, 10Y, DXY, and VIX reactions at 5m/15m/30m/60m as associations, not causal claims. Combine similar-news retrieval with event type, regime, time, and relevance.

Free AI tiers may allow provider use of submitted content for product improvement. Never send brokerage credentials, account IDs, personal financial information, or secret API keys to an AI provider.

Environment defaults: `FOREX_FACTORY_ENABLED=true`, `MARKETAUX_ENABLED=true`, `BLS_ENABLED=true`, `FEDERAL_RESERVE_ENABLED=true`, `BEA_ENABLED=true`, `NEWS_POLL_INTERVAL_ACTIVE=60`, `NEWS_POLL_INTERVAL_IDLE=300`, `NEWS_MIN_NQ_RELEVANCE=0.50`, and `NEWS_HIGH_IMPACT_THRESHOLD=0.75`.

## Point-in-time rules

Use `published_at`/released availability, not ingestion time alone. At prediction time T, later articles, later corrections, future reactions, and revised event interpretations are unavailable. News impact models must use the market state known at publication and store the exact model/version used for extraction.
