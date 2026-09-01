## When to read this file

Read for Marketaux, Fed RSS, SEC news/event ingestion, NLP extraction, relevance scoring, and news point-in-time rules.

# News Data

## Sources and free-tier approach

Use Marketaux Free rather than Benzinga for V1: approximately $0/month, 100 requests/day, three articles/request, metadata, entity tracking, and global financial news. Query Nasdaq, technology, semiconductors, AI, mega-cap tech, monetary policy, inflation, Treasury yields, and geopolitical shocks. Maintain a high-impact universe: NVDA, MSFT, AAPL, AMZN, GOOGL, META, AVGO, TSLA, AMD, NFLX.

Also ingest Federal Reserve RSS/pages for decisions, policy releases, speeches, testimony, and press releases. Use SEC EDGAR, prioritizing 8-K filings for major Nasdaq weights; later include 10-Q and 10-K.

## Polling and storage

Do not poll continuously. Suggested ET polls are 06:00, 07:00, 08:00, 08:25, 08:45, 09:15, 09:25, 10:00, 12:00, 14:00, and 15:30. Batch requests where supported. Deduplicate by URL/provider UUID, store all fetched stories, and queue NLP once; do not repeatedly fetch the same story.

## Normalized event

Each `NewsArticle` becomes a strict-enum `NewsEvent` with article ID, event type, event timestamp, stance, NQ direction, relevance, surprise, confidence, summary, reason, model version, and creation time. Extract headline, published time, source, entities, topics, directional impact for NQ/US10Y/USD, and impact horizon. Initial event types are Fed decision/speech, CPI/PPI/PCE/NFP/jobless claims/GDP/PMI/ISM/retail sales, earnings/guidance, AI/semiconductor/regulation/M&A/product launch/cybersecurity, geopolitical/energy/China macro, Treasury yield move, dollar move, and other.

## NQ relevance

Calculate `nq_relevance_score` in `[0,1]` from source reliability, ticker/index relevance, Nasdaq weight, macro importance, novelty, surprise, recency, and historical market sensitivity. The starting heuristic is entity relevance .25, macro importance .20, surprise .20, recency .15, source quality .10, historical sensitivity .10; it is not permanent.

## NLP and news ML

Hide model access behind `LLMProvider` (`extract_event`, `summarize`, `reason_bias`) and support Gemini first, with OpenAI, Anthropic, and Ollama adapters later. Store embeddings for headlines/summaries/structured descriptions when introduced. Record post-event NQ/ES, 10Y, DXY, and VIX reactions at 5m/15m/30m/60m as associations, not causal claims. Combine similar-news retrieval with event type, regime, time, and relevance.

Free AI tiers may allow provider use of submitted content for product improvement. Never send brokerage credentials, account IDs, personal financial information, or secret API keys to an AI provider.

## Point-in-time rules

Use `published_at`/released availability, not ingestion time alone. At prediction time T, later articles, later corrections, future reactions, and revised event interpretations are unavailable. News impact models must use the market state known at publication and store the exact model/version used for extraction.
