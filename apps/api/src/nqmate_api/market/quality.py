"""Conservative canonical-minute coverage audit, separate from dataset certification."""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite
from typing import Sequence

from nqmate_api.market.calculations import EASTERN
from nqmate_api.market.models import MarketBar, MarketContract

QUALITY_VERSION = "minute-coverage-v2.1"


def session_window(session_date: date) -> tuple[datetime, datetime]:
    """Existing full-session convention; unknown holidays/short days fail closed."""
    return (
        datetime.combine(session_date - timedelta(days=1), time(18), EASTERN).astimezone(timezone.utc),
        datetime.combine(session_date, time(16), EASTERN).astimezone(timezone.utc),
    )


@dataclass(frozen=True)
class SessionQualityReport:
    session_date: date
    contract: str
    quality_version: str
    expected_minutes: int
    observed_minutes: int
    missing_timestamps: tuple[datetime, ...]
    issue_counts: dict[str, int]

    @property
    def eligible(self) -> bool:
        return not self.issue_counts


def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def audit_session_bars(
    bars: Sequence[MarketBar], session_date: date, contract: MarketContract,
) -> SessionQualityReport:
    """Audit one raw contract; no imputation, deduplication or price adjustment.

    Retrieval after the historical session is permitted here. Snapshot eligibility
    needs a separate point-in-time policy and is NOT certified by this audit.
    """
    start, end = session_window(session_date)
    minute = timedelta(minutes=1)
    expected = {start + i * minute for i in range(int((end - start) / minute))}
    seen: Counter[datetime] = Counter()
    issues: Counter[str] = Counter()
    for bar in bars:
        if bar.timeframe != "1min":
            continue
        if not _aware(bar.timestamp):
            issues["invalid_timestamp"] += 1
            continue
        timestamp = bar.timestamp.astimezone(timezone.utc)
        if not start <= timestamp < end:
            continue
        if bar.symbol != contract.raw_contract_symbol:
            issues["contract_mismatch"] += 1
            continue
        if timestamp.second or timestamp.microsecond:
            issues["unaligned_minute"] += 1
            continue
        seen[timestamp] += 1
        values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        if (not all(isfinite(value) for value in values)
                or not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high
                or min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume < 0):
            issues["invalid_ohlcv"] += 1
        if (not _aware(bar.available_at) or not _aware(bar.ingested_at)
                or bar.available_at < timestamp + minute):
            issues["invalid_availability"] += 1
    missing = tuple(sorted(expected - seen.keys()))
    if missing:
        issues["missing_minutes"] = len(missing)
    duplicates = sum(count - 1 for count in seen.values())
    if duplicates:
        issues["duplicate_minutes"] = duplicates
    return SessionQualityReport(
        session_date, contract.raw_contract_symbol, QUALITY_VERSION,
        len(expected), len(seen), missing, dict(sorted(issues.items())),
    )
