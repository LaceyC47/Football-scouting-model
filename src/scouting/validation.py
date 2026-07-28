from __future__ import annotations

import pandas as pd


CORE_COLUMNS = [
    "player",
    "club",
    "competition",
    "season",
    "minutes",
]


def build_quality_report(frame: pd.DataFrame) -> pd.DataFrame:
    """Create one quality-summary row per column."""
    row_count = len(frame)
    rows = []

    for column in frame.columns:
        missing = int(frame[column].isna().sum())
        rows.append({
            "column": column,
            "rows": row_count,
            "non_null": row_count - missing,
            "missing": missing,
            "missing_pct": round((missing / row_count * 100), 2) if row_count else 0.0,
            "unique_values": int(frame[column].nunique(dropna=True)),
            "is_core_column": column in CORE_COLUMNS,
        })

    return pd.DataFrame(rows).sort_values(
        ["is_core_column", "missing_pct", "column"],
        ascending=[False, False, True],
    )


def rows_for_review(frame: pd.DataFrame, minimum_minutes: int) -> pd.DataFrame:
    """Return records needing human review."""
    conditions = pd.Series(False, index=frame.index)

    for column in ["player", "club", "competition"]:
        if column not in frame.columns:
            conditions = pd.Series(True, index=frame.index)
        else:
            conditions |= frame[column].isna()

    if "minutes" in frame.columns:
        conditions |= frame["minutes"].isna()
        conditions |= frame["minutes"] < 0

    conditions |= frame.duplicated("player_season_id", keep=False)

    review = frame.loc[conditions].copy()
    if "minutes" in review.columns:
        review["below_model_minutes"] = review["minutes"] < minimum_minutes
    return review
