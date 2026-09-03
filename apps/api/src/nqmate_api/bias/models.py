from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BiasSnapshot:
    overnight_structure: float
    gap: float
    technical_location: float
    relative_strength: float
    macro_context: float
    news_context: float
    minutes_to_high_impact_event: float | None
    analogue_bull_rate: float | None = None
    analogue_avg_30m_return: float | None = None
    analogue_avg_60m_return: float | None = None
    analogue_sample_size: int | None = None


@dataclass(frozen=True)
class BiasResult:
    direction: str
    score: float
    confidence: float
    recommendation: str
    catalyst_risk: str | None
    evidence: tuple[str, ...] = ()
    bull_case: tuple[str, ...] = ()
    bear_case: tuple[str, ...] = ()
    invalidation: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
