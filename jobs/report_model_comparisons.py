"""Print read-only champion/challenger comparisons from the ML registry."""

from __future__ import annotations

import argparse
import json

from nqmate_api.config import Settings
from nqmate_api.ml.calibration import champion_challenger_report
from nqmate_api.ml.repository import SupabaseMlRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Report gated champion/challenger model comparisons")
    parser.add_argument("--target")
    args = parser.parse_args()
    models = SupabaseMlRepository.from_settings(Settings()).list_models(args.target)
    print(json.dumps(champion_challenger_report(models), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
