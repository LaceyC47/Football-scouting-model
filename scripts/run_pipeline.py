from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scouting.pipeline import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the master football scouting player-season database."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "pipeline.yml",
        help="Path to pipeline configuration.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        result = run_pipeline(args.config, PROJECT_ROOT)
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1

    print("Pipeline completed successfully.")
    print(f"Input files: {result['input_files']}")
    print(f"Master rows: {result['master_rows']}")
    print(f"Failed files: {result['failures']}")
    print(f"Master database: {result['master_path']}")
    print(f"Quality report: {result['quality_path']}")
    print(f"Review file: {result['review_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
