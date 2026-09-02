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
