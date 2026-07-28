"""Metric identification and classification utilities."""

from __future__ import annotations

import re
import pandas as pd


IDENTITY_COLUMNS = {
    "Rk", "Player", "Nation", "Pos", "Squad", "Comp", "Age", "Born"
}

PLAYING_TIME_PATTERNS = (
    r"^MP", r"^Starts", r"^Min", r"^90s", r"Mn/", r"Min%", r"Compl",
    r"Subs", r"unSub", r"PPM"
)
DEFENDING_PATTERNS = (
    r"^Tkl", r"^Int", r"^Fls", r"^Fld", r"^Crd", r"^2CrdY$", r"^OG$",
    r"^GA", r"^CS", r"^Save", r"^SoTA", r"^PKA", r"^PKsv", r"^PKm"
)
SHOOTING_PATTERNS = (
    r"^Gls", r"^Ast", r"^G\+A", r"^G-PK", r"^PK$", r"^PKatt",
    r"^Sh", r"^SoT", r"^G/Sh", r"^G/SoT"
)
TEAM_IMPACT_PATTERNS = (r"^onG$", r"^onGA$", r"^\+/-", r"^On-Off$")


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, name, flags=re.IGNORECASE) for pattern in patterns)


def classify_metric(column: str) -> str:
    if column in IDENTITY_COLUMNS or column.startswith((
        "Nation_stats_", "Pos_stats_", "Comp_stats_", "Age_stats_", "Born_stats_", "Rk_stats_"
    )):
        return "identity_or_duplicate_metadata"
    if _matches(column, PLAYING_TIME_PATTERNS):
        return "playing_time"
    if _matches(column, DEFENDING_PATTERNS):
        return "defending_or_goalkeeping"
    if _matches(column, SHOOTING_PATTERNS):
        return "shooting_or_output"
    if _matches(column, TEAM_IMPACT_PATTERNS):
        return "team_impact"
    if column == "Crs":
        return "crossing"
    if column == "Off":
        return "offside"
    return "unclassified"


def infer_unit(column: str) -> str:
    lowered = column.lower()
    if "%" in column:
        return "percentage"
    if "/90" in column or lowered.endswith("90"):
        return "per_90"
    if column in {"Age", "Born", "Rk"} or column.startswith(("Age_", "Born_", "Rk_")):
        return "identifier_or_year"
    if column.startswith("Min") or column == "Mn/MP":
        return "minutes"
    return "count_or_rate_unknown"


def is_numeric_like(series: pd.Series, threshold: float = 0.90) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    non_null = series.dropna()
    if non_null.empty:
        return False
    converted = pd.to_numeric(
        non_null.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce"
    )
    return float(converted.notna().mean()) >= threshold


def modelling_suitability(column: str, category: str, numeric_like: bool) -> str:
    if category == "identity_or_duplicate_metadata":
        return "metadata"
    if not numeric_like:
        return "not_numeric"
    if category in {
        "playing_time", "defending_or_goalkeeping", "shooting_or_output",
        "team_impact", "crossing", "offside"
    }:
        return "candidate"
    return "review"
