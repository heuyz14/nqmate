from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strategy:
    name: str
    description: str
    allowed_regimes: tuple[str, ...]
    required_conditions: tuple[str, ...]
    confirmation_conditions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    entry_logic: str
    target_logic: str
    stop_logic: str
    active: bool
