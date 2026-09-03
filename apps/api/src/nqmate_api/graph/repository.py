from __future__ import annotations

from typing import Protocol

from neo4j import Driver, GraphDatabase

from nqmate_api.config import Settings
from nqmate_api.graph.ontology import RegimeDimensions, constraints, sync_session_query


class GraphRepository(Protocol):
    def ensure_schema(self) -> None: ...
    def sync_session(self, session_date: str, dimensions: RegimeDimensions) -> None: ...


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

    def close(self) -> None:
        self.driver.close()
