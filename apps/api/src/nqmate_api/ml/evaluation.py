from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from typing import Sequence

from nqmate_api.analogues.models import HistoricalSession
from nqmate_api.ml.baselines import LabeledRow
from nqmate_api.ml.metrics import evaluate_walk_forward


def rows_from_sessions(sessions: Sequence[HistoricalSession], outcome_name: str) -> tuple[LabeledRow, ...]:
    rows: list[LabeledRow] = []
    for session in sessions:
        outcome = session.outcomes.get(outcome_name)
        if not isinstance(outcome, (int, float)):
            continue
        feature_names = sorted(name for name, value in session.features.items() if isinstance(value, (int, float)))
        values = tuple(float(session.features[name]) for name in feature_names)
        if not values:
            continue
        session_date = date.fromisoformat(session.session_date)
        timestamp = datetime.combine(session_date, time(9, 30), ZoneInfo("America/New_York")).astimezone(timezone.utc)
        rows.append(LabeledRow(timestamp, session.available_at, values, int(float(outcome) > 0), session.features.get("overnight_return")))
    return tuple(sorted(rows, key=lambda row: row.feature_timestamp))


def evaluate_sessions(sessions: Sequence[HistoricalSession], outcome_name: str = "return_30m", min_train_size: int = 20) -> dict[str, dict[str, float | None]]:
    rows = rows_from_sessions(sessions, outcome_name)
    if len(rows) <= min_train_size:
        return {}
    return evaluate_walk_forward(rows, min_train_size=min_train_size)
