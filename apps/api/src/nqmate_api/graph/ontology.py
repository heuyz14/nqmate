from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeDimensions:
    overnight_direction: str
    overnight_volatility: str
    gap: str
    location: str
    yield_regime: str
    catalyst_regime: str

    def as_properties(self) -> dict[str, str]:
        return {
            "overnight_direction": self.overnight_direction,
            "overnight_volatility": self.overnight_volatility,
            "gap": self.gap,
            "location": self.location,
            "yield_regime": self.yield_regime,
            "catalyst_regime": self.catalyst_regime,
        }


def constraints() -> tuple[str, ...]:
    return (
        "CREATE CONSTRAINT market_session_date IF NOT EXISTS FOR (n:MarketSession) REQUIRE n.session_date IS UNIQUE",
        "CREATE CONSTRAINT market_regime_key IF NOT EXISTS FOR (n:MarketRegime) REQUIRE n.key IS UNIQUE",
        "CREATE CONSTRAINT asset_symbol IF NOT EXISTS FOR (n:Asset) REQUIRE n.symbol IS UNIQUE",
    )


def sync_session_query() -> str:
    return """
    MERGE (market_session:MarketSession {session_date: $session_date})
    MERGE (regime:MarketRegime {key: $regime_key})
    SET regime += $regime_properties
    MERGE (market_session)-[:CLASSIFIED_AS]->(regime)
    """
