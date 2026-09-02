from __future__ import annotations

from nqmate_api.macro.models import ScheduledRelease
from nqmate_api.news.models import CalendarImpact, EconomicCalendarEvent

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
