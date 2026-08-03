from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
from collections import Counter, defaultdict

import pandas as pd
import pyarrow.parquet as pq


SOURCE_PREFIXES = {
    "sofascore_match_info__": "sofascore_match_info",
    "sofascore_match_momentum__": "sofascore_match_momentum",
    "sofascore_match_player_stats__": "sofascore_match_player_stats",
    "sofascore_match_shots__": "sofascore_match_shots",
    "sofascore_match_team_stats__": "sofascore_match_team_stats",
    "sofascore__": "sofascore_season",
    "transfermarkt__": "transfermarkt",
    "understat_league_table__": "understat_league_table",
    "understat_match_info__": "understat_match_info",
    "understat_match_shots__": "understat_match_shots",
    "understat_rosters__": "understat_rosters",
    "understat__": "understat_season",
    "clubelo__": "clubelo",
}


def classify_source(filename: str) -> str:
    for prefix, source in SOURCE_PREFIXES.items():
        if filename.startswith(prefix):
            return source
    return "other"


def parse_filename(filename: str) -> dict[str, str | None]:
    stem = filename.removesuffix(".parquet")
    source = classify_source(filename)
    remainder = stem

    for prefix in SOURCE_PREFIXES:
        if stem.startswith(prefix):
            remainder = stem[len(prefix):]
            break

    season_match = re.search(r"(20\d{2}_20\d{2})", remainder)
    season = season_match.group(1).replace("_", "-") if season_match else None

    competition = remainder
    if season_match:
        competition = remainder[:season_match.start()].rstrip("_")
    competition = competition.replace("__", "_").replace("_", " ").strip() or None

    return {
        "source_type": source,
        "competition": competition,
        "season": season,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_parquet(path: Path, sample_rows: int = 5) -> tuple[dict, list[dict], list[dict]]:
    parsed = parse_filename(path.name)
    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow
    metadata = parquet.metadata

    file_row = {
        "filename": path.name,
        "full_path": str(path),
        "source_type": parsed["source_type"],
        "competition": parsed["competition"],
        "season": parsed["season"],
        "rows": metadata.num_rows,
        "columns": len(schema),
        "row_groups": metadata.num_row_groups,
        "size_mb": round(path.stat().st_size / 1_000_000, 3),
        "modified_utc": pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat(),
        "sha256": sha256_file(path),
        "status": "ok",
        "error": None,
    }

    column_rows = []
    for field in schema:
        column_rows.append({
            "filename": path.name,
            "source_type": parsed["source_type"],
            "competition": parsed["competition"],
            "season": parsed["season"],
            "column": field.name,
            "arrow_type": str(field.type),
            "nullable": field.nullable,
        })

    sample_rows_out = []
    try:
        sample = pd.read_parquet(path).head(sample_rows)
        for idx, row in sample.iterrows():
            sample_rows_out.append({
                "filename": path.name,
                "sample_row_number": len(sample_rows_out) + 1,
                "sample_json": row.to_json(date_format="iso", default_handler=str),
            })
    except Exception as exc:
        sample_rows_out.append({
            "filename": path.name,
            "sample_row_number": 0,
            "sample_json": json.dumps({"sample_error": str(exc)}),
        })

    return file_row, column_rows, sample_rows_out


def build_inventory(raw_dir: Path, output_dir: Path, sample_rows: int = 5) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(raw_dir.glob("*.parquet"))

    file_rows = []
    column_rows = []
    sample_rows_all = []

    for index, path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] {path.name}")
        try:
            file_row, columns, samples = inventory_parquet(path, sample_rows)
            file_rows.append(file_row)
            column_rows.extend(columns)
            sample_rows_all.extend(samples)
        except Exception as exc:
            parsed = parse_filename(path.name)
            file_rows.append({
                "filename": path.name,
                "full_path": str(path),
                "source_type": parsed["source_type"],
                "competition": parsed["competition"],
                "season": parsed["season"],
                "rows": None,
                "columns": None,
                "row_groups": None,
                "size_mb": round(path.stat().st_size / 1_000_000, 3),
                "modified_utc": pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat(),
                "sha256": None,
                "status": "error",
                "error": str(exc),
            })

    files_df = pd.DataFrame(file_rows)
    columns_df = pd.DataFrame(column_rows)
    samples_df = pd.DataFrame(sample_rows_all)

    if not columns_df.empty:
        frequencies = (
            columns_df.groupby("column")
            .agg(
                file_count=("filename", "nunique"),
                source_count=("source_type", "nunique"),
                source_types=("source_type", lambda s: " | ".join(sorted(set(s)))),
                example_files=("filename", lambda s: " | ".join(list(dict.fromkeys(s))[:5])),
            )
            .reset_index()
            .sort_values(["file_count", "column"], ascending=[False, True])
        )
    else:
        frequencies = pd.DataFrame(columns=[
            "column", "file_count", "source_count", "source_types", "example_files"
        ])

    summary_rows = [
        ("parquet_files", len(files_df)),
        ("successful_files", int((files_df["status"] == "ok").sum()) if not files_df.empty else 0),
        ("failed_files", int((files_df["status"] == "error").sum()) if not files_df.empty else 0),
        ("total_rows_across_files", int(files_df["rows"].fillna(0).sum()) if not files_df.empty else 0),
        ("unique_columns", int(columns_df["column"].nunique()) if not columns_df.empty else 0),
        ("source_types", int(files_df["source_type"].nunique()) if not files_df.empty else 0),
        ("competitions", int(files_df["competition"].nunique(dropna=True)) if not files_df.empty else 0),
        ("seasons", int(files_df["season"].nunique(dropna=True)) if not files_df.empty else 0),
        ("total_size_mb", round(float(files_df["size_mb"].sum()), 2) if not files_df.empty else 0),
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["metric", "value"])

    source_summary = (
        files_df.groupby("source_type", dropna=False)
        .agg(
            files=("filename", "count"),
            rows=("rows", "sum"),
            columns_max=("columns", "max"),
            size_mb=("size_mb", "sum"),
            errors=("status", lambda s: int((s == "error").sum())),
        )
        .reset_index()
        .sort_values("files", ascending=False)
    )

    outputs = {
        "dataset_inventory.csv": files_df,
        "column_inventory.csv": columns_df,
        "column_frequency.csv": frequencies,
        "sample_rows.csv": samples_df,
        "inventory_summary.csv": summary_df,
        "source_summary.csv": source_summary,
    }

    result_paths = {}
    for name, frame in outputs.items():
        path = output_dir / name
        frame.to_csv(path, index=False)
        result_paths[name] = path

    return result_paths
