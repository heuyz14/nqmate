from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev
from datetime import datetime
from typing import Sequence

from nqmate_api.analogues.models import AnalogueMatch, HistoricalSession


def _scale(rows: Sequence[HistoricalSession], names: Sequence[str]) -> tuple[dict[str, float], dict[str, float]]:
    means = {name: mean(row.features[name] for row in rows) for name in names}
    deviations = {name: pstdev(row.features[name] for row in rows) or 1.0 for name in names}
    return means, deviations


def _summary(matches: Sequence[HistoricalSession]) -> dict[str, float]:
    returns = [row.outcomes["return_30m"] for row in matches if isinstance(row.outcomes.get("return_30m"), (int, float))]
    onh = [row.outcomes["onh_first"] for row in matches if isinstance(row.outcomes.get("onh_first"), bool)]
    return {
        "return_30m_mean": round(mean(returns), 10) if returns else 0.0,
        "onh_first_rate": round(sum(onh) / len(onh), 10) if onh else 0.0,
        "sample_size": float(len(matches)),
    }


def rank_analogues(current_session_date: str, current_features: dict[str, float], history: Sequence[HistoricalSession], prediction_time: datetime, top_k: int = 20, metric: str = "euclidean") -> list[AnalogueMatch]:
    if top_k < 1 or metric not in {"euclidean", "cosine"}:
        raise ValueError("top_k must be positive and metric must be euclidean or cosine")
    candidates = [row for row in history if row.session_date < current_session_date and row.available_at <= prediction_time]
    names = tuple(sorted(current_features))
    candidates = [row for row in candidates if all(name in row.features for name in names)]
    if not candidates:
        return []
    means, deviations = _scale(candidates, names)
    current = [(current_features[name] - means[name]) / deviations[name] for name in names]
    scored: list[tuple[float, HistoricalSession]] = []
    for candidate in candidates:
        vector = [(candidate.features[name] - means[name]) / deviations[name] for name in names]
        if metric == "euclidean":
            distance = sqrt(sum((left - right) ** 2 for left, right in zip(current, vector)))
        else:
            denominator = sqrt(sum(value * value for value in current) * sum(value * value for value in vector))
            distance = 1.0 if denominator == 0 else 1 - sum(left * right for left, right in zip(current, vector)) / denominator
        scored.append((round(distance, 10), candidate))
    scored.sort(key=lambda item: (item[0], item[1].session_date))
    selected = [item[1] for item in scored[:top_k]]
    summary = _summary(selected)
    return [AnalogueMatch(row.session_date, distance, summary) for distance, row in scored[:top_k]]
