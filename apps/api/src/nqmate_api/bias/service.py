from __future__ import annotations

from nqmate_api.bias.models import BiasResult, BiasSnapshot

_WEIGHTS = {
    "overnight_structure": 0.20, "gap": 0.10, "technical_location": 0.20,
    "relative_strength": 0.15, "macro_context": 0.20, "news_context": 0.15,
}


def _validate(snapshot: BiasSnapshot) -> None:
    values = (snapshot.overnight_structure, snapshot.gap, snapshot.technical_location,
              snapshot.relative_strength, snapshot.macro_context, snapshot.news_context)
    if any(value < -1 or value > 1 for value in values):
        raise ValueError("bias inputs must be normalized to [-1, 1]")


def score_bias(snapshot: BiasSnapshot) -> BiasResult:
    _validate(snapshot)
    score = round(sum(getattr(snapshot, name) * weight for name, weight in _WEIGHTS.items()), 6)
    direction = "BULLISH" if score >= 0.15 else "BEARISH" if score <= -0.15 else "NEUTRAL"
    confidence = round(min(0.95, abs(score)), 6)
    minutes = snapshot.minutes_to_high_impact_event
    catalyst_risk = None
    recommendation = "MONITOR"
    if minutes is not None and 0 <= minutes <= 15:
        catalyst_risk = "CRITICAL_EVENT_RISK"
        confidence = min(confidence, 0.55)
        recommendation = "WAIT_FOR_RELEASE"
    return BiasResult(direction, score, confidence, recommendation, catalyst_risk)
