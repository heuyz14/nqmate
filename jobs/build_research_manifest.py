"""Build an immutable local manifest from a market certification report."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def build_manifest(certification: dict, *, source_hash: str, git_commit: str) -> dict:
    summary = certification["summary"]
    sessions = certification.get("sessions", [])
    products = sorted({row["product"] for row in sessions})
    dates = sorted({row["session_date"] for row in sessions})
    quarantined = int(summary.get("quarantined", 0))
    return {
        "manifest_version": "research-v2-freeze-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
        "products": products,
        "session_count": len(sessions),
        "eligible_sessions": int(summary.get("eligible", 0)),
        "schedule_adjusted_sessions": int(summary.get("schedule_adjusted_complete", 0)),
        "closure_sessions": int(summary.get("not_a_trading_session", 0)),
        "quarantined_sessions": quarantined,
        "certified": quarantined == 0,
        "source_hash": source_hash,
        "git_commit": git_commit,
        "quality_scope": certification.get("scope"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certification", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.certification.read_bytes()
    certification = json.loads(raw)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    manifest = build_manifest(certification, source_hash=hashlib.sha256(raw).hexdigest(), git_commit=commit)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
