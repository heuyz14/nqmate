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
    if snapshot.analogue_bull_rate is not None and not 0 <= snapshot.analogue_bull_rate <= 1:
        raise ValueError("analogue bull rate must be between 0 and 1")
    if snapshot.analogue_sample_size is not None and snapshot.analogue_sample_size < 0:
        raise ValueError("analogue sample size must not be negative")


def score_bias(snapshot: BiasSnapshot) -> BiasResult:
    _validate(snapshot)
    score = round(sum(getattr(snapshot, name) * weight for name, weight in _WEIGHTS.items()), 6)
    direction = "BULLISH" if score >= 0.15 else "BEARISH" if score <= -0.15 else "NEUTRAL"
    confidence = round(min(0.95, abs(score)), 6)
    minutes = snapshot.minutes_to_high_impact_event
    catalyst_risk = None
    recommendation = "MONITOR"
    evidence = tuple(name for name in _WEIGHTS if getattr(snapshot, name) != 0)
    bull_case = tuple(name for name in _WEIGHTS if getattr(snapshot, name) > 0)
    bear_case = tuple(name for name in _WEIGHTS if getattr(snapshot, name) < 0)
    invalidation = ("score crosses the neutral threshold",)
    uncertainty = ("score magnitude is limited",) if abs(score) < 0.35 else ()
    if snapshot.analogue_bull_rate is not None:
        rate = snapshot.analogue_bull_rate
        if rate >= 0.55:
            evidence = evidence + (f"historical analogues favor bullish outcomes ({rate:.1%} up)",)
        elif rate <= 0.45:
            evidence = evidence + (f"historical analogues favor bearish outcomes ({1 - rate:.1%} down)",)
        else:
            uncertainty = uncertainty + ("historical analogues are directionally mixed",)
    if snapshot.analogue_avg_30m_return is not None:
        label = "bull_case" if snapshot.analogue_avg_30m_return > 0 else "bear_case"
        text = f"analogue 30m mean return is {snapshot.analogue_avg_30m_return:+.2%}"
        if label == "bull_case":
            bull_case = bull_case + (text,)
        else:
            bear_case = bear_case + (text,)
    if snapshot.analogue_avg_60m_return is not None:
        label = "bull_case" if snapshot.analogue_avg_60m_return > 0 else "bear_case"
        text = f"analogue 60m mean return is {snapshot.analogue_avg_60m_return:+.2%}"
        if label == "bull_case":
            bull_case = bull_case + (text,)
        else:
            bear_case = bear_case + (text,)
    if snapshot.analogue_sample_size is not None:
        uncertainty = uncertainty + (f"historical analogue sample size: {snapshot.analogue_sample_size}",)
    if minutes is not None and 0 <= minutes <= 15:
        catalyst_risk = "CRITICAL_EVENT_RISK"
        confidence = min(confidence, 0.55)
        recommendation = "WAIT_FOR_RELEASE"
        uncertainty = uncertainty + ("high-impact catalyst is within 15 minutes",)
    return BiasResult(direction, score, confidence, recommendation, catalyst_risk, evidence, bull_case, bear_case, invalidation, uncertainty)
