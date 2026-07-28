"""Dataset audit and defensive-midfielder pool generation."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

from .metrics import classify_metric, infer_unit, is_numeric_like, modelling_suitability
from .positions import add_position_flags


def load_dataset(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duplicate_metadata_groups(columns: list[str]) -> pd.DataFrame:
    rows = []
    canonical_names = ["Rk", "Nation", "Pos", "Comp", "Age", "Born", "MP", "Starts", "Min", "90s"]
    for canonical in canonical_names:
        matches = [c for c in columns if c == canonical or c.startswith(f"{canonical}_stats_")]
        if len(matches) > 1:
            rows.append({
                "canonical_field": canonical,
                "column_count": len(matches),
                "columns": " | ".join(matches),
            })
    return pd.DataFrame(rows)


def build_column_profile(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in frame.columns:
        series = frame[column]
        numeric_like = is_numeric_like(series)
        category = classify_metric(column)
        rows.append({
            "column": column,
            "dtype": str(series.dtype),
            "non_null": int(series.notna().sum()),
            "missing": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 2),
            "unique": int(series.nunique(dropna=True)),
            "numeric_like": bool(numeric_like),
            "category": category,
            "inferred_unit": infer_unit(column),
            "modelling_suitability": modelling_suitability(column, category, numeric_like),
        })
    return pd.DataFrame(rows)


def build_duplicate_report(frame: pd.DataFrame) -> pd.DataFrame:
    candidate_keys = [
        ["Player", "Squad", "Comp"],
        ["Player", "Squad", "Comp", "Born"],
    ]
    rows = []
    for keys in candidate_keys:
        available = [k for k in keys if k in frame.columns]
        if not available:
            continue
        duplicate_mask = frame.duplicated(subset=available, keep=False)
        rows.append({
            "key": " + ".join(available),
            "duplicate_rows": int(duplicate_mask.sum()),
            "duplicate_groups": int(
                frame.loc[duplicate_mask].groupby(available, dropna=False).ngroups
                if duplicate_mask.any() else 0
            ),
        })
    rows.append({
        "key": "full_row",
        "duplicate_rows": int(frame.duplicated(keep=False).sum()),
        "duplicate_groups": int(frame.loc[frame.duplicated(keep=False)].drop_duplicates().shape[0]),
    })
    return pd.DataFrame(rows)


def build_position_breakdown(frame: pd.DataFrame) -> pd.DataFrame:
    if "Pos" not in frame.columns:
        return pd.DataFrame(columns=["Pos", "players", "minutes"])
    work = frame.copy()
    work["Min_numeric"] = pd.to_numeric(work.get("Min"), errors="coerce")
    return (
        work.groupby("Pos", dropna=False)
        .agg(players=("Player", "size"), minutes=("Min_numeric", "sum"))
        .reset_index()
        .sort_values(["players", "minutes"], ascending=[False, False])
    )


def add_per90_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    nineties = pd.to_numeric(result.get("90s"), errors="coerce")
    for source in ["TklW", "Int", "Fls", "Fld", "CrdY", "CrdR", "Crs", "Off"]:
        if source in result.columns:
            values = pd.to_numeric(result[source], errors="coerce")
            result[f"{source}_per90"] = np.where(nineties > 0, values / nineties, np.nan)
    return result


def build_dm_pool(
    frame: pd.DataFrame,
    minimum_minutes: int = 900,
    preferred_minimum_minutes: int = 1500,
    min_age: int = 18,
    max_age: int = 29,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = add_position_flags(frame)
    work["Min_numeric"] = pd.to_numeric(work.get("Min"), errors="coerce")
    work["Age_numeric"] = pd.to_numeric(work.get("Age"), errors="coerce")
    work = add_per90_metrics(work)

    broad = work[
        work["is_midfielder"]
        & work["Min_numeric"].ge(minimum_minutes)
        & work["Age_numeric"].between(min_age, max_age, inclusive="both")
    ].copy()

    pure = broad[broad["is_pure_midfielder"]].copy()

    for pool in (broad, pure):
        pool["meets_preferred_minutes"] = pool["Min_numeric"].ge(preferred_minimum_minutes)

    sort_columns = [c for c in ["Min_numeric", "Player"] if c in broad.columns]
    if sort_columns:
        broad = broad.sort_values(sort_columns, ascending=[False, True])
        pure = pure.sort_values(sort_columns, ascending=[False, True])

    return broad, pure


def dataset_summary(frame: pd.DataFrame, input_path: str | Path, broad, pure) -> pd.DataFrame:
    age = pd.to_numeric(frame.get("Age"), errors="coerce")
    minutes = pd.to_numeric(frame.get("Min"), errors="coerce")
    rows = [
        ("input_file", str(input_path)),
        ("sha256", file_sha256(input_path)),
        ("rows", len(frame)),
        ("columns", len(frame.columns)),
        ("unique_players", int(frame["Player"].nunique()) if "Player" in frame else None),
        ("unique_squads", int(frame["Squad"].nunique()) if "Squad" in frame else None),
        ("unique_competitions", int(frame["Comp"].nunique()) if "Comp" in frame else None),
        ("age_min", float(age.min()) if age.notna().any() else None),
        ("age_max", float(age.max()) if age.notna().any() else None),
        ("minutes_median", float(minutes.median()) if minutes.notna().any() else None),
        ("broad_midfielder_pool", len(broad)),
        ("pure_midfielder_pool", len(pure)),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def run_audit(
    input_path: str | Path,
    output_directory: str | Path,
    minimum_minutes: int = 900,
    preferred_minimum_minutes: int = 1500,
    min_age: int = 18,
    max_age: int = 29,
) -> dict[str, pd.DataFrame]:
    frame = load_dataset(input_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    broad, pure = build_dm_pool(
        frame,
        minimum_minutes=minimum_minutes,
        preferred_minimum_minutes=preferred_minimum_minutes,
        min_age=min_age,
        max_age=max_age,
    )

    outputs = {
        "dataset_summary": dataset_summary(frame, input_path, broad, pure),
        "column_profile": build_column_profile(frame),
        "duplicate_report": build_duplicate_report(frame),
        "duplicate_metadata_groups": duplicate_metadata_groups(frame.columns.tolist()),
        "position_breakdown": build_position_breakdown(frame),
        "dm_pool_broad": broad,
        "dm_pool_pure": pure,
    }

    for name, result in outputs.items():
        result.to_csv(output_directory / f"{name}.csv", index=False)

    return outputs
