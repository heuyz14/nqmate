from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class HistoricalSession:
    session_date: str
    features: dict[str, float]
    available_at: datetime
    outcomes: dict[str, Any]


@dataclass(frozen=True)
class AnalogueMatch:
    session_date: str
    distance: float
    outcome_summary: dict[str, float]
