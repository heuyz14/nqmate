from nqmate_api.strategies.models import Strategy


def validate_strategy(strategy: Strategy) -> None:
    if not strategy.name.strip():
        raise ValueError("strategy name is required")
    if not strategy.entry_logic.strip() or not strategy.target_logic.strip() or not strategy.stop_logic.strip():
        raise ValueError("entry, target, and stop logic are required")
