from dataclasses import dataclass


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str


class Neo4jConnection:
    """Server-side boundary for Neo4j; graph operations arrive in Phase 6."""

    def __init__(self, config: Neo4jConfig) -> None:
        self.config = config

