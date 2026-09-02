from __future__ import annotations

from nqmate_api.macro.models import ScheduledRelease
from nqmate_api.news.models import CalendarImpact, EconomicCalendarEvent
from typing import Sequence

from nqmate_api.macro.models import MacroObservation

_HIGH_IMPACT_RELEASES = (
    "employment situation", "consumer price index", "producer price index",
    "job openings and labor turnover", "unemployment", "nonfarm payroll",
)


def release_to_calendar_event(release: ScheduledRelease) -> EconomicCalendarEvent:
    title = release.title.strip()
    impact = CalendarImpact.HIGH if any(term in title.lower() for term in _HIGH_IMPACT_RELEASES) else CalendarImpact.MEDIUM
    return EconomicCalendarEvent(
        event=title, currency="USD", impact=impact, scheduled_at=release.scheduled_at, source="bls",
    )


def persist_observations(repository: object, observations: Sequence[MacroObservation]) -> int:
    for observation in observations:
        repository.upsert(observation)
    return len(observations)


def event_surprise(event: EconomicCalendarEvent) -> float | None:
    if event.actual is None or event.forecast is None:
        return None
    return round(event.actual - event.forecast, 10)


def link_release_timestamp(repository: object, observation: MacroObservation, release: ScheduledRelease) -> None:
    """Link only an explicit observation/release pair; never infer the period."""
    repository.set_released_at(observation.series_id, observation.period, release.scheduled_at)


def interpret_surprise(event_name: str, surprise: float) -> dict[str, str]:
    """Translate a numeric surprise through the event's NQ/rates semantics."""
    name = event_name.lower()
    inflation = any(term in name for term in ("cpi", "ppi", "pce", "inflation"))
    labor = any(term in name for term in ("employment", "payroll", "job openings", "unemployment", "jobs"))
    growth = any(term in name for term in ("gdp", "retail sales", "consumer confidence"))
    if inflation or labor:
        direction = "BEARISH" if surprise > 0 else "BULLISH" if surprise < 0 else "NEUTRAL"
        rationale = "hotter/stronger data may raise rates and pressure growth-stock valuations" if surprise > 0 else "cooler/weaker data may reduce rate pressure on growth-stock valuations" if surprise < 0 else "release matched expectations"
    elif growth:
        direction = "BULLISH" if surprise > 0 else "BEARISH" if surprise < 0 else "NEUTRAL"
        rationale = "stronger/weaker growth signal changes the growth outlook; rate effects require context"
    else:
        direction, rationale = "UNKNOWN", "no event-specific NQ surprise mapping is configured"
    return {"expected_nq_direction": direction, "interpretation": rationale}
