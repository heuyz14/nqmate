from __future__ import annotations

import argparse
import asyncio
from datetime import date

from nqmate_api.analogues.repository import SupabaseAnalogueRepository
from nqmate_api.config import Settings
from nqmate_api.ml.evaluation import evaluate_sessions, rows_from_sessions, target_name
from nqmate_api.ml.models import DatasetRecord, ModelRecord
from nqmate_api.ml.repository import SupabaseMlRepository


async def run(start: date, end: date, outcome_name: str = "return_30m", min_train_size: int = 20) -> dict[str, dict[str, float | None]]:
    analogue = SupabaseAnalogueRepository.from_settings(Settings())
    sessions = [item for item in analogue.list(1000) if start.isoformat() <= item.session_date <= end.isoformat()]
    metrics = evaluate_sessions(sessions, outcome_name=outcome_name, min_train_size=min_train_size)
    if not metrics:
        return {}
    rows = rows_from_sessions(sessions, outcome_name)
    registry = SupabaseMlRepository.from_settings(Settings())
    output_target = target_name(outcome_name)
    dataset_version = f"analogue-{output_target}-{start.isoformat()}-{end.isoformat()}-v1"
    registry.upsert_dataset(DatasetRecord(
        version=dataset_version, target=output_target, feature_version="analogue-v1",
        row_count=len(rows), start_date=start.isoformat(), end_date=end.isoformat(),
    ))
    existing_names = {str(row.get("name")) for row in registry.list_models(output_target)}
    for name, values in metrics.items():
        model_name = f"baseline-{name}-{output_target}-{end.isoformat()}"
        if model_name in existing_names:
            continue
        registry.create_model(ModelRecord(
            name=model_name, target=output_target,
            algorithm=name, algorithm_version="builtin-v1", feature_version="analogue-v1",
            dataset_version=dataset_version, metrics=values,
            hyperparameters={"min_train_size": min_train_size}, artifact_path=f"builtin://{name}",
            training_start=start.isoformat(), training_end=end.isoformat(), active=False,
        ))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate leakage-aware ML baselines on historical analogue data")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--outcome-name", default="return_30m")
    parser.add_argument("--min-train-size", type=int, default=20)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(asyncio.run(run(args.start, args.end, args.outcome_name, args.min_train_size)), flush=True)


if __name__ == "__main__":
    main()
