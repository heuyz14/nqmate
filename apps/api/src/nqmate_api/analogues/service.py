from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev
from datetime import datetime, time, timedelta, timezone
from typing import Sequence

from nqmate_api.analogues.models import AnalogueMatch, HistoricalSession
from nqmate_api.market.models import MarketSession
from nqmate_api.market.models import MarketBar
from nqmate_api.market.calculations import EASTERN


def _scale(rows: Sequence[HistoricalSession], names: Sequence[str]) -> tuple[dict[str, float], dict[str, float]]:
    means = {name: mean(row.features[name] for row in rows) for name in names}
    deviations = {name: pstdev(row.features[name] for row in rows) or 1.0 for name in names}
    return means, deviations


def _summary(matches: Sequence[HistoricalSession]) -> dict[str, float]:
    def numeric_values(name: str) -> list[float]:
        return [float(row.outcomes[name]) for row in matches if isinstance(row.outcomes.get(name), (int, float))]

    def numeric_mean(name: str) -> float:
        values = numeric_values(name)
        return round(mean(values), 10) if values else 0.0

    def boolean_rate(name: str) -> float:
        values = [row.outcomes[name] for row in matches if isinstance(row.outcomes.get(name), bool)]
        return round(sum(values) / len(values), 10) if values else 0.0

    returns = [row.outcomes["return_60m"] for row in matches if isinstance(row.outcomes.get("return_60m"), (int, float))]

    def numeric_range(name: str) -> dict[str, float]:
        values = numeric_values(name)
        return {f"{name}_min": round(min(values), 10), f"{name}_max": round(max(values), 10)} if values else {f"{name}_min": 0.0, f"{name}_max": 0.0}

    return {"analogue_bull_rate": round(sum(value > 0 for value in returns) / len(returns), 10) if returns else 0.0,
            "return_30m_mean": numeric_mean("return_30m"), "return_60m_mean": numeric_mean("return_60m"),
            "open_close_mean": numeric_mean("open_close"), "onh_first_rate": boolean_rate("onh_first"),
            "onl_first_rate": boolean_rate("onl_first"), "trend_day_rate": boolean_rate("trend_day"),
            "sample_size": float(len(matches)), **numeric_range("return_30m"), **numeric_range("return_60m"),
            **numeric_range("open_close")}


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
    summary = _summary([item[1] for item in scored[:top_k]])
    return [AnalogueMatch(row.session_date, distance, summary) for distance, row in scored[:top_k]]


def session_features(session: MarketSession) -> dict[str, float]:
    """Build analogue inputs from fields known by the regular-session open."""
    return {
        "overnight_return": session.overnight_return or 0.0,
        "overnight_range": session.overnight_range,
        "gap_pct": session.gap_pct or 0.0,
        "atr_14": session.atr_14 or 0.0,
        "prior_day_high_distance": (session.overnight_high - session.prior_day_high) if session.prior_day_high is not None else 0.0,
        "prior_day_low_distance": (session.overnight_low - session.prior_day_low) if session.prior_day_low is not None else 0.0,
    }


def session_outcomes(session: MarketSession, bars: Sequence[MarketBar]) -> dict[str, float | bool]:
    regular_start = datetime.combine(session.session_date, time(9, 30), EASTERN).astimezone(timezone.utc)
    regular_end = datetime.combine(session.session_date, time(16, 0), EASTERN).astimezone(timezone.utc)
    regular = sorted((bar for bar in bars if regular_start <= bar.timestamp < regular_end), key=lambda bar: bar.timestamp)
    if not regular or regular[0].open == 0:
        return {}
    base = regular[0].open
    outcomes: dict[str, float | bool] = {"open_close": regular[-1].close / base - 1}
    for minutes in (5, 15, 30, 60, 120, 240):
        target = regular[0].timestamp + timedelta(minutes=minutes)
        bar = next((item for item in regular if item.timestamp >= target), None)
        if bar is not None:
            outcomes[f"return_{minutes}m"] = bar.close / base - 1
    onh_break = next((bar for bar in regular if bar.high >= session.overnight_high), None)
    onl_break = next((bar for bar in regular if bar.low <= session.overnight_low), None)
    if onh_break is not None or onl_break is not None:
        outcomes["onh_first"] = onh_break is not None and (onl_break is None or onh_break.timestamp < onl_break.timestamp)
        outcomes["onl_first"] = onl_break is not None and (onh_break is None or onl_break.timestamp < onh_break.timestamp)
    session_range = max(bar.high for bar in regular) - min(bar.low for bar in regular)
    if session_range:
        close_location = (regular[-1].close - min(bar.low for bar in regular)) / session_range
        outcomes["trend_day"] = close_location >= 0.8 or close_location <= 0.2
    return outcomes
