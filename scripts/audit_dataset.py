"""Run Milestone 3 dataset audit.

Usage:
    python scripts/audit_dataset.py
    python scripts/audit_dataset.py --input data/raw/players_data-2025_2026.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scouting.audit import run_audit


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/raw/players_data-2025_2026.csv",
        help="Path to CSV or Excel dataset.",
    )
    parser.add_argument("--output", default="reports")
    parser.add_argument("--minimum-minutes", type=int, default=900)
    parser.add_argument("--preferred-minimum-minutes", type=int, default=1500)
    parser.add_argument("--min-age", type=int, default=18)
    parser.add_argument("--max-age", type=int, default=29)
    return parser.parse_args()


def main():
    args = parse_args()
    outputs = run_audit(
        input_path=ROOT / args.input,
        output_directory=ROOT / args.output,
        minimum_minutes=args.minimum_minutes,
        preferred_minimum_minutes=args.preferred_minimum_minutes,
        min_age=args.min_age,
        max_age=args.max_age,
    )

    summary = outputs["dataset_summary"]
    print("Milestone 3 audit completed successfully.")
    for _, row in summary.iterrows():
        print(f"{row['metric']}: {row['value']}")


if __name__ == "__main__":
    main()
