from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

import pandas as pd


def snake_case(value: Any) -> str:
    """Convert a column label to a stable snake_case name."""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[%/]+", "_per_", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def normalise_text(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else pd.NA


def build_alias_lookup(column_aliases: dict[str, list[str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in column_aliases.items():
        lookup[snake_case(canonical)] = snake_case(canonical)
        for alias in aliases:
            lookup[snake_case(alias)] = snake_case(canonical)
    return lookup


def standardise_columns(
    frame: pd.DataFrame,
    column_aliases: dict[str, list[str]],
) -> pd.DataFrame:
    """Standardise labels and apply configured aliases."""
    result = frame.copy()
    result.columns = [snake_case(column) for column in result.columns]

    lookup = build_alias_lookup(column_aliases)
    rename_map = {
        column: lookup[column]
        for column in result.columns
        if column in lookup
    }
    result = result.rename(columns=rename_map)

    # Avoid duplicate labels after aliases are applied.
    result = result.loc[:, ~result.columns.duplicated(keep="first")]
    return result


def clean_player_data(
    frame: pd.DataFrame,
    column_aliases: dict[str, list[str]],
    season: str,
) -> pd.DataFrame:
    result = standardise_columns(frame, column_aliases)

    for column in ["player", "club", "competition", "position", "source_file", "source_sheet"]:
        if column in result.columns:
            result[column] = result[column].map(normalise_text)

    numeric_columns = [
        "age", "minutes", "nineties",
        "tackles_won_per90", "interceptions_per90", "fouls_per90",
        "yellow_cards_per90", "red_cards_per90",
    ]
    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")

    if "minutes" in result.columns:
        calculated_nineties = result["minutes"] / 90
        if "nineties" not in result.columns:
            result["nineties"] = calculated_nineties
        else:
            result["nineties"] = result["nineties"].fillna(calculated_nineties)

    result["season"] = season
    result["player_id"] = result.apply(_make_player_id, axis=1)
    result["player_season_id"] = result.apply(_make_player_season_id, axis=1)

    required = ["player", "club", "competition"]
    result["data_quality_flag"] = result.apply(
        lambda row: "review" if any(pd.isna(row.get(field)) for field in required)
        else "complete",
        axis=1,
    )
    return result


def _hash_key(parts: list[Any]) -> str:
    value = "|".join("" if pd.isna(part) else str(part).strip().lower() for part in parts)
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def _make_player_id(row: pd.Series) -> str:
    return _hash_key([row.get("player"), row.get("club")])


def _make_player_season_id(row: pd.Series) -> str:
    return _hash_key([
        row.get("player"),
        row.get("club"),
        row.get("competition"),
        row.get("season"),
    ])
