from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def read_file(path: Path, sheet: str | None) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    raise ValueError("Use a CSV, XLSX or XLSM file.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quickly profile one football dataset.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--sheet", default=None)
    args = parser.parse_args()

    frame = read_file(args.path, args.sheet)
    print(f"Rows: {len(frame):,}")
    print(f"Columns: {len(frame.columns):,}")
    print("\nColumns:")
    for column in frame.columns:
        missing = frame[column].isna().mean() * 100
        print(f"- {column}: {missing:.1f}% missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
