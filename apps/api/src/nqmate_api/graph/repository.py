from __future__ import annotations

from typing import Protocol

from neo4j import Driver, GraphDatabase

from nqmate_api.config import Settings
from nqmate_api.graph.ontology import RegimeDimensions, constraints, sync_session_query


class GraphRepository(Protocol):
    def ensure_schema(self) -> None: ...
    def sync_session(self, session_date: str, dimensions: RegimeDimensions) -> None: ...
    def sync_news_event(self, provider: str, provider_id: str, event_type: str, event_timestamp: str, available_at: str, relevance: float, direction: str, themes: tuple[str, ...], companies: tuple[str, ...]) -> None: ...
    def sync_macro_event(self, event_id: str, title: str, scheduled_at: str, available_at: str, impact: str) -> None: ...
    def sync_prediction(self, prediction_id: str, created_at: str, direction: str, score: float, confidence: float, session_date: str | None = None) -> None: ...
    def query_regimes(self, filters: dict[str, str], limit: int = 20) -> list[dict[str, object]]: ...
    def sync_outcome(self, outcome_id: str, prediction_id: str, observed_at: str, instrument: str, horizon: str, return_pct: float | None) -> None: ...
    def query_strategy_evidence(self, filters: dict[str, str], limit: int = 20) -> list[dict[str, object]]: ...


class Neo4jGraphRepository:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    @classmethod
    def from_settings(cls, settings: Settings) -> "Neo4jGraphRepository":
        if not settings.neo4j_uri or not settings.neo4j_username or not settings.neo4j_password:
            raise ValueError("Neo4j configuration is required")
        return cls(GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password)))

    def ensure_schema(self) -> None:
        with self.driver.session() as session:
            for query in constraints():
                session.run(query)

    def sync_session(self, session_date: str, dimensions: RegimeDimensions) -> None:
        properties = dimensions.as_properties()
        regime_key = "|".join(properties.values())
        with self.driver.session() as session:
            session.run(
                sync_session_query(), session_date=session_date,
                regime_key=regime_key, regime_properties=properties,
            )

    def sync_news_event(self, provider: str, provider_id: str, event_type: str, event_timestamp: str, available_at: str, relevance: float, direction: str, themes: tuple[str, ...], companies: tuple[str, ...]) -> None:
        query = """
        MERGE (event:NewsEvent {key: $event_key})
        SET event.event_type = $event_type, event.event_timestamp = $event_timestamp,
            event.available_at = $available_at, event.nq_relevance = $relevance,
            event.direction = $direction, event.themes = $themes
        WITH event
        UNWIND $companies AS company_name
        MERGE (company:Company {name: company_name})
        MERGE (event)-[:MENTIONS]->(company)
        """
        with self.driver.session() as session:
            session.run(
                query, event_key=f"{provider}:{provider_id}", event_type=event_type,
                event_timestamp=event_timestamp, available_at=available_at,
                relevance=relevance, direction=direction, themes=list(themes), companies=list(companies),
            )

    def sync_prediction(self, prediction_id: str, created_at: str, direction: str, score: float, confidence: float, session_date: str | None = None) -> None:
        query = """
        MERGE (prediction:Prediction {id: $prediction_id})
        SET prediction.created_at = $created_at, prediction.direction = $direction,
            prediction.score = $score, prediction.confidence = $confidence
        WITH prediction
        OPTIONAL MATCH (market_session:MarketSession {session_date: $session_date})
        FOREACH (_ IN CASE WHEN market_session IS NULL THEN [] ELSE [1] END |
            MERGE (prediction)-[:MADE_DURING]->(market_session))
        """
        with self.driver.session() as session:
            session.run(
                query, prediction_id=prediction_id, created_at=created_at,
                direction=direction, score=score, confidence=confidence,
                session_date=session_date,
            )

    def sync_macro_event(self, event_id: str, title: str, scheduled_at: str, available_at: str, impact: str) -> None:
        query = """
        MERGE (event:MacroEvent {id: $event_id})
        SET event.title = $title, event.scheduled_at = $scheduled_at,
            event.available_at = $available_at, event.impact = $impact
        """
        with self.driver.session() as session:
            session.run(
                query, event_id=event_id, title=title, scheduled_at=scheduled_at,
                available_at=available_at, impact=impact,
            )

    def query_regimes(self, filters: dict[str, str], limit: int = 20) -> list[dict[str, object]]:
        query = """
        MATCH (market_session:MarketSession)-[:CLASSIFIED_AS]->(regime:MarketRegime)
        WHERE all(name IN keys($filters) WHERE regime[name] = $filters[name])
        RETURN market_session.session_date AS session_date, properties(regime) AS regime
        ORDER BY market_session.session_date DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            return session.run(query, filters=filters, limit=limit).data()

    def sync_outcome(self, outcome_id: str, prediction_id: str, observed_at: str, instrument: str, horizon: str, return_pct: float | None) -> None:
        query = """
        MERGE (prediction:Prediction {id: $prediction_id})
        MERGE (outcome:Outcome {id: $outcome_id})
        SET outcome.observed_at = $observed_at, outcome.instrument = $instrument,
            outcome.horizon = $horizon, outcome.return_pct = $return_pct
        MERGE (prediction)-[:RESULTED_IN]->(outcome)
        """
        with self.driver.session() as session:
            session.run(
                query, outcome_id=outcome_id, prediction_id=prediction_id,
                observed_at=observed_at, instrument=instrument, horizon=horizon,
                return_pct=return_pct,
            )

    def query_strategy_evidence(self, filters: dict[str, str], limit: int = 20) -> list[dict[str, object]]:
        query = """
        MATCH (strategy:Strategy)-[:PERFORMS_WELL_IN]->(regime:MarketRegime)
        WHERE all(name IN keys($filters) WHERE regime[name] = $filters[name])
        RETURN strategy.name AS strategy, strategy.sample_size AS sample_size,
               strategy.win_rate AS win_rate, strategy.expectancy AS expectancy,
               properties(regime) AS regime
        ORDER BY strategy.expectancy DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            return session.run(query, filters=filters, limit=limit).data()

    def close(self) -> None:
        self.driver.close()
