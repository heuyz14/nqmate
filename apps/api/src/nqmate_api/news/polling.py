from datetime import datetime, time
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def polling_interval_seconds(now: datetime, active: int = 60, idle: int = 300) -> int:
    """Return the configured cadence for the highest-priority ET windows."""
    eastern = now.astimezone(EASTERN).time()
    active_windows = (time(8, 0) <= eastern <= time(10, 30), time(14, 0) <= eastern <= time(16, 0))
    return active if any(active_windows) else idle
