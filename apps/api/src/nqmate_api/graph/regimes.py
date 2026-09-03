from __future__ import annotations

from nqmate_api.graph.ontology import RegimeDimensions
from nqmate_api.market.models import MarketSession

_STRONG_OVERNIGHT_RETURN = 0.005
_FLAT_GAP_PCT = 0.001
_LOW_RANGE_RATIO = 1.0
_HIGH_RANGE_RATIO = 2.0
_EXTREME_RANGE_RATIO = 3.0


def _overnight_direction(value: float) -> str:
    if value >= _STRONG_OVERNIGHT_RETURN:
        return "STRONG_UP"
    if value > 0:
        return "UP"
    if value <= -_STRONG_OVERNIGHT_RETURN:
        return "STRONG_DOWN"
    if value < 0:
        return "DOWN"
    return "FLAT"


def _overnight_volatility(overnight_range: float, atr_14: float | None) -> str:
    if not atr_14:
        return "NORMAL"
    ratio = overnight_range / atr_14
    if ratio < _LOW_RANGE_RATIO:
        return "LOW"
    if ratio < _HIGH_RANGE_RATIO:
        return "NORMAL"
    if ratio < _EXTREME_RANGE_RATIO:
        return "HIGH"
    return "EXTREME"


def _gap(gap_pct: float | None) -> str:
    if gap_pct is None or abs(gap_pct) <= _FLAT_GAP_PCT:
        return "FLAT_OPEN"
    return "GAP_UP" if gap_pct > 0 else "GAP_DOWN"


def _location(session: MarketSession) -> str:
    if session.prior_day_high is None or session.prior_day_low is None:
        return "INSIDE_PRIOR_RANGE"
    if session.overnight_low > session.prior_day_high:
        return "ABOVE_PRIOR_RANGE"
    if session.overnight_high < session.prior_day_low:
        return "BELOW_PRIOR_RANGE"
    return "INSIDE_PRIOR_RANGE"


def classify_market_regime(
    session: MarketSession,
    *,
    yield_change: float | None = None,
    high_impact_events: int = 0,
    minutes_to_event: float | None = None,
    recently_released: bool = False,
) -> RegimeDimensions:
    """Classify a session with explicit v0 thresholds and neutral missing-signal defaults."""
    yield_regime = "YIELDS_FLAT" if yield_change is None or abs(yield_change) <= _FLAT_GAP_PCT else ("YIELDS_UP" if yield_change > 0 else "YIELDS_DOWN")
    if high_impact_events > 1:
        catalyst_regime = "MULTIPLE_HIGH_IMPACT_EVENTS"
    elif recently_released:
        catalyst_regime = "POST_EVENT"
    elif minutes_to_event is not None and minutes_to_event >= 0:
        catalyst_regime = "PRE_EVENT"
    else:
        catalyst_regime = "NO_MAJOR_EVENT"
    return RegimeDimensions(
        _overnight_direction(session.overnight_return or 0.0),
        _overnight_volatility(session.overnight_range, session.atr_14),
        _gap(session.gap_pct),
        _location(session),
        yield_regime,
        catalyst_regime,
    )
