from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StrategyOutcome:
    setup_id: str
    strategy_id: str
    session_date: str
    observed_at: datetime
    return_pct: float | None
    mfe: float | None = None
    mae: float | None = None
    regime: str | None = None
