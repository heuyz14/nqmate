from __future__ import annotations

from nqmate_api.news.models import NewsArticle


NQ_UNIVERSE = {"NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "AMD", "NFLX"}
MACRO_TERMS = {"federal reserve", "fed", "inflation", "cpi", "ppi", "pce", "nfp", "treasury", "yield", "dollar"}


def nq_relevance_score(article: NewsArticle) -> float:
    text = f"{article.headline} {article.summary or ''}".lower()
    entities = {entity.upper() for entity in article.entities}
    entity_score = 1.0 if entities & NQ_UNIVERSE else 0.0
    macro_score = 1.0 if any(term in text for term in MACRO_TERMS) else 0.0
    topic_score = min(len(article.topics) / 3, 1.0)
    source_score = 1.0 if article.source else 0.0
    return round(min(1.0, entity_score * 0.25 + macro_score * 0.20 + topic_score * 0.20 + source_score * 0.10), 6)
