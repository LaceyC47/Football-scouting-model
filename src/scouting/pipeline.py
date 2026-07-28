from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .cleaning import clean_player_data
from .io import discover_input_files, read_table
from .validation import build_quality_report, rows_for_review


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def run_pipeline(config_path: Path, project_root: Path) -> dict[str, Path | int]:
    config = load_config(config_path)

    raw_dir = project_root / config["paths"]["raw_data"]
    processed_dir = project_root / config["paths"]["processed_data"]
    export_dir = project_root / config["paths"]["exports"]
    processed_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    input_files = discover_input_files(raw_dir)
    if not input_files:
        raise FileNotFoundError(
            f"No CSV or Excel files found in {raw_dir}. "
            "Copy a source dataset into data/raw and run the pipeline again."
        )

    cleaned_frames = []
    failures = []

    for path in input_files:
        try:
            raw = read_table(path, config["project"].get("preferred_sheet"))
            cleaned = clean_player_data(
                raw,
                config["column_aliases"],
                config["project"]["season"],
            )
            cleaned_frames.append(cleaned)
        except Exception as exc:  # Preserve a useful batch error report.
            failures.append({"source_file": path.name, "error": str(exc)})

    if not cleaned_frames:
        raise RuntimeError(f"All input files failed: {failures}")

    master = pd.concat(cleaned_frames, ignore_index=True, sort=False)
    master = master.drop_duplicates("player_season_id", keep="first")

    preferred_order = [
        "player_season_id", "player_id", "player", "club", "competition",
        "season", "position", "age", "minutes", "nineties",
        "data_quality_flag", "source_file", "source_sheet",
    ]
    existing = [column for column in preferred_order if column in master.columns]
    remaining = [column for column in master.columns if column not in existing]
    master = master[existing + remaining]

    master_path = processed_dir / config["output"]["master_csv"]
    quality_path = export_dir / config["output"]["quality_csv"]
    review_path = export_dir / config["output"]["review_csv"]
    failure_path = export_dir / "ingestion_failures.csv"

    master.to_csv(master_path, index=False)
    build_quality_report(master).to_csv(quality_path, index=False)
    rows_for_review(
        master,
        config["project"]["minimum_minutes"],
    ).to_csv(review_path, index=False)
    pd.DataFrame(failures, columns=["source_file", "error"]).to_csv(failure_path, index=False)

    return {
        "input_files": len(input_files),
        "master_rows": len(master),
        "master_path": master_path,
        "quality_path": quality_path,
        "review_path": review_path,
        "failures": len(failures),
    }
