from __future__ import annotations

import argparse
from datetime import date, datetime, time, timezone

from nqmate_api.bias.repository import BiasRepository, SupabaseBiasRepository
from nqmate_api.config import Settings
from nqmate_api.graph.repository import GraphRepository, Neo4jGraphRepository
from nqmate_api.news.repository import NewsRepository, SupabaseNewsRepository


def _in_range(value: str, start: date, end: date) -> bool:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return start <= parsed.date() <= end


def sync_sources(start: date, end: date, news: NewsRepository, bias: BiasRepository, graph: GraphRepository) -> dict[str, int]:
    graph.ensure_schema()
    counts = {"news": 0, "macro": 0, "predictions": 0}
    start_at = datetime.combine(start, time.min, timezone.utc).isoformat()
    end_at = datetime.combine(end, time.max, timezone.utc).isoformat()
    for item in news.list_events(limit=100, start=start_at, end=end_at):
        article = item.get("news_articles") or {}
        if not article.get("provider") or not article.get("provider_id"):
            continue
        graph.sync_news_event(
            provider=article["provider"], provider_id=article["provider_id"],
            event_type=item.get("event_type", "other"), event_timestamp=item["event_timestamp"],
            available_at=article.get("available_at", item["event_timestamp"]),
            relevance=float(item.get("nq_relevance_score") or 0), direction=item.get("nq_direction", "unknown"),
            themes=tuple(item.get("themes") or ()), companies=tuple(article.get("entities") or ()),
        )
        counts["news"] += 1
    for item in news.list_calendar_events(start_at, end_at, limit=100):
        graph.sync_macro_event(
            event_id=f"{item.get('provider')}:{item.get('provider_event_id')}", title=item.get("event", "unknown"),
            scheduled_at=item["scheduled_at"], available_at=item.get("available_at", item["scheduled_at"]),
            impact=item.get("impact", "UNKNOWN"),
        )
        counts["macro"] += 1
    for item in bias.history(limit=100):
        created_at = item.get("created_at")
        if created_at and _in_range(created_at, start, end):
            graph.sync_prediction(
                prediction_id=item["id"], created_at=created_at, direction=item["direction"],
                score=float(item["score"]), confidence=float(item["confidence"]), session_date=item.get("session_date"),
            )
            counts["predictions"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync normalized source records into Neo4j semantic memory")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    settings = Settings()
    news = SupabaseNewsRepository.from_settings(settings)
    bias = SupabaseBiasRepository.from_settings(settings)
    graph = Neo4jGraphRepository.from_settings(settings)
    try:
        print(f"graph sources synced: {sync_sources(args.start, args.end, news, bias, graph)}", flush=True)
    finally:
        graph.close()


if __name__ == "__main__":
    main()
