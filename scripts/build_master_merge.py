from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scouting.master_merge import build_master


def main() -> int:
    config_path = ROOT / "config" / "master_merge_config.json"
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    raw_dir = Path(config["raw_data_directory"])
    if not raw_dir.exists():
        print(f"ERROR: Raw data directory not found: {raw_dir}")
        return 1

    paths = build_master(
        raw_dir=raw_dir,
        output_dir=ROOT / config["output_directory"],
        report_dir=ROOT / config["report_directory"],
        seasons=config.get("seasons"),
        competitions=config.get("include_competitions"),
        min_match_minutes=int(config.get("minimum_match_minutes_for_aggregation", 1)),
        fuzzy_threshold=int(config.get("fuzzy_match_threshold", 92)),
        fuzzy_review_threshold=int(config.get("fuzzy_review_threshold", 84)),
        write_csv=bool(config.get("write_csv", True)),
    )

    print("\nMaster merge complete.")
    for label, path in paths.items():
        print(f"- {label}: {path}")
    print("- reports: reports\\merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
