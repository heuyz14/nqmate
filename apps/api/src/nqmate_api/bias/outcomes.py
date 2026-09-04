from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


HORIZON_OUTCOMES = ("return_5m", "return_15m", "return_30m", "return_60m", "return_120m", "return_240m", "open_close")


@dataclass(frozen=True)
class PredictionOutcome:
    prediction_id: str
    session_date: date
    horizon: str
    realized_return: float
    realized_direction: bool
    correct: bool | None
    observed_at: datetime


def attach_outcomes(
    prediction: Mapping[str, Any], session_date: date, outcomes: Mapping[str, Any], observed_at: datetime
) -> tuple[PredictionOutcome, ...]:
    """Attach only explicit, numeric realized outcomes to a stored prediction."""
    prediction_id = str(prediction.get("id", ""))
    if not prediction_id:
        raise ValueError("prediction id is required")
    direction = str(prediction.get("direction", "")).upper()
    result: list[PredictionOutcome] = []
    for horizon in HORIZON_OUTCOMES:
        value = outcomes.get(horizon)
        if not isinstance(value, (int, float)):
            continue
        realized_return = float(value)
        realized_direction = realized_return > 0
        correct = realized_direction if direction == "BULLISH" else not realized_direction if direction == "BEARISH" else None
        result.append(PredictionOutcome(
            prediction_id, session_date, horizon, realized_return, realized_direction, correct, observed_at,
        ))
    return tuple(result)
