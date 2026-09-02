from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MacroObservation:
    series_id: str
    period: str
    value: float
    released_at: datetime | None
    retrieved_at: datetime
    vintage_date: datetime | None

    def is_available_by(self, timestamp: datetime) -> bool:
        """Require an explicit release time when evaluating historical availability."""
        available_at = self.released_at or self.retrieved_at
        return available_at <= timestamp
