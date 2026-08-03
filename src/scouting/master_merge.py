from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import hashlib
import json
import math
import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process


# ---------- General helpers ----------

def normalise_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = text.replace("ø", "o").replace("ð", "d").replace("þ", "th")
    text = re.sub(r"\b(fc|cf|afc|ssc|ac|fk|sc|sv|rcd|rc|calcio|club)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_key(value: object) -> str:
    return normalise_text(value).replace(" ", "")


def safe_numeric(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def read_parquets(raw_dir: Path, pattern: str) -> pd.DataFrame:
    files = sorted(raw_dir.glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = []
    for path in files:
        try:
            frame = pd.read_parquet(path)
            frame["_source_file"] = path.name
            frames.append(frame)
        except Exception as exc:
            print(f"WARNING: Failed to read {path.name}: {exc}")
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def stable_player_id(name: object, dob: object = None) -> str:
    payload = f"{normalise_text(name)}|{str(dob) if dob is not None else ''}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def season_start_year(season: object) -> float:
    match = re.match(r"(\d{4})", str(season or ""))
    return float(match.group(1)) if match else np.nan


def canonicalise_competition(value: object) -> str:
    key = normalise_text(value)
    mapping = {
        "england premier league": "England Premier League",
        "premier league": "England Premier League",
        "england efl championship": "England EFL Championship",
        "efl championship": "England EFL Championship",
        "championship": "England EFL Championship",
        "france ligue 1": "France Ligue 1",
        "ligue 1": "France Ligue 1",
        "germany bundesliga": "Germany Bundesliga",
        "bundesliga": "Germany Bundesliga",
        "italy serie a": "Italy Serie A",
        "serie a": "Italy Serie A",
        "spain la liga": "Spain La Liga",
        "la liga": "Spain La Liga",
        "netherlands eredivisie": "Netherlands Eredivisie",
        "eredivisie": "Netherlands Eredivisie",
        "portugal primeira liga": "Portugal Primeira Liga",
        "primeira liga": "Portugal Primeira Liga",
        "uefa champions league": "UEFA Champions League",
        "champions league": "UEFA Champions League",
        "uefa europa league": "UEFA Europa League",
        "europa league": "UEFA Europa League",
    }
    return mapping.get(key, str(value).strip() if value is not None else "")


def canonicalise_team(value: object) -> str:
    aliases = {
        "man utd": "Manchester United",
        "manchester utd": "Manchester United",
        "man city": "Manchester City",
        "spurs": "Tottenham Hotspur",
        "tottenham": "Tottenham Hotspur",
        "wolves": "Wolverhampton Wanderers",
        "inter": "Inter Milan",
        "internazionale": "Inter Milan",
        "psg": "Paris Saint-Germain",
        "paris sg": "Paris Saint-Germain",
        "bayern munich": "Bayern München",
        "bayern munchen": "Bayern München",
        "athletic bilbao": "Athletic Club",
    }
    key = normalise_text(value)
    return aliases.get(key, str(value).strip() if value is not None else "")


def make_match_key(frame: pd.DataFrame, name_col: str, team_col: str, league_col: str, season_col: str) -> pd.Series:
    return (
        frame[name_col].map(compact_key)
        + "|"
        + frame[team_col].map(lambda x: compact_key(canonicalise_team(x)))
        + "|"
        + frame[league_col].map(lambda x: compact_key(canonicalise_competition(x)))
        + "|"
        + frame[season_col].astype(str)
    )


# ---------- Source preparation ----------

def prepare_sofascore_season(raw_dir: Path) -> pd.DataFrame:
    df = read_parquets(raw_dir, "sofascore__*.parquet")
    if df.empty:
        return df

    df = df.rename(columns={
        "player": "player_name",
        "team": "team_name",
        "league": "competition",
    })
    df["competition"] = df["competition"].map(canonicalise_competition)
    df["team_name"] = df["team_name"].map(canonicalise_team)
    df["name_norm"] = df["player_name"].map(normalise_text)
    df["team_norm"] = df["team_name"].map(normalise_text)

    rename = {}
    for column in df.columns:
        if column not in {
            "player_name", "team_name", "competition", "season", "name_norm",
            "team_norm", "sofascore_id", "sofascore_team_id", "_source_file"
        }:
            rename[column] = f"sofa_{column}"
    df = df.rename(columns=rename)

    keep_first = [
        "player_name", "team_name", "competition", "season",
        "name_norm", "team_norm", "sofascore_id", "sofascore_team_id", "_source_file"
    ]
    return df[[c for c in keep_first if c in df.columns] + [c for c in df.columns if c not in keep_first]]


MATCH_SUM_COLUMNS = [
    "minutesPlayed", "totalPass", "accuratePass", "totalLongBalls", "accurateLongBalls",
    "accurateOwnHalfPasses", "totalOwnHalfPasses", "accurateOppositionHalfPasses",
    "totalOppositionHalfPasses", "totalCross", "accurateCross", "aerialWon", "aerialLost",
    "duelWon", "duelLost", "totalClearance", "ballRecovery", "totalTackle", "wonTackle",
    "interceptionWon", "challengeLost", "dispossessed", "totalContest", "wonContest",
    "unsuccessfulTouch", "touches", "possessionLostCtrl", "keyPass", "goalAssist",
    "bigChanceCreated", "bigChanceMissed", "totalShots", "onTargetScoringAttempt",
    "shotOffTarget", "blockedScoringAttempt", "goals", "fouls", "wasFouled",
    "totalOffside", "expectedGoals", "expectedAssists", "expectedGoalsOnTarget",
    "ballCarriesCount", "progressiveBallCarriesCount", "totalBallCarriesDistance",
    "totalProgressiveBallCarriesDistance", "totalProgression", "numberOfSprints",
    "kilometersCovered", "metersCoveredWalkingKm", "metersCoveredJoggingKm",
    "metersCoveredRunningKm", "metersCoveredHighSpeedRunningKm",
    "metersCoveredSprintingKm", "errorLeadToAGoal", "errorLeadToAShot",
    "lastManTackle", "penaltyWon", "penaltyConceded", "ownGoals"
]


def prepare_sofascore_match_aggregates(raw_dir: Path, min_minutes: int = 1) -> pd.DataFrame:
    df = read_parquets(raw_dir, "sofascore_match_player_stats__*.parquet")
    if df.empty:
        return df

    df = safe_numeric(df, MATCH_SUM_COLUMNS + ["rating", "player_id", "teamId", "height"])
    df = df[df.get("minutesPlayed", 0).fillna(0) >= min_minutes].copy()
    df["competition"] = df["league"].map(canonicalise_competition)
    df["team_name"] = df["teamName"].map(canonicalise_team)
    df["player_name"] = df["player_name"].fillna(df.get("shortName"))
    df["name_norm"] = df["player_name"].map(normalise_text)
    df["team_norm"] = df["team_name"].map(normalise_text)

    group_cols = ["player_id", "player_name", "team_name", "competition", "season", "name_norm", "team_norm"]
    available_sum = [c for c in MATCH_SUM_COLUMNS if c in df.columns]

    agg_spec = {c: "sum" for c in available_sum}
    if "rating" in df.columns:
        df["_rating_minutes"] = df["rating"] * df["minutesPlayed"].fillna(0)
        agg_spec["_rating_minutes"] = "sum"
    if "height" in df.columns:
        agg_spec["height"] = "max"
    if "dateOfBirthTimestamp" in df.columns:
        agg_spec["dateOfBirthTimestamp"] = "max"
    if "position" in df.columns:
        agg_spec["position"] = lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else np.nan
    if "proposedMarketValueRaw" in df.columns:
        agg_spec["proposedMarketValueRaw"] = lambda s: s.dropna().iloc[-1] if not s.dropna().empty else np.nan
    if "country" in df.columns:
        agg_spec["country"] = lambda s: s.dropna().iloc[-1] if not s.dropna().empty else np.nan

    grouped = df.groupby(group_cols, dropna=False).agg(agg_spec).reset_index()
    if "_rating_minutes" in grouped.columns and "minutesPlayed" in grouped.columns:
        grouped["match_weighted_rating"] = grouped["_rating_minutes"] / grouped["minutesPlayed"].replace(0, np.nan)
        grouped = grouped.drop(columns=["_rating_minutes"])

    grouped["match_appearances"] = (
        df.groupby(group_cols, dropna=False)["match_id"].nunique().reset_index(drop=True)
    )

    # Derived efficiency rates from raw match totals.
    rate_pairs = {
        "pass_completion_pct": ("accuratePass", "totalPass"),
        "long_ball_completion_pct": ("accurateLongBalls", "totalLongBalls"),
        "own_half_pass_completion_pct": ("accurateOwnHalfPasses", "totalOwnHalfPasses"),
        "opposition_half_pass_completion_pct": ("accurateOppositionHalfPasses", "totalOppositionHalfPasses"),
        "cross_completion_pct": ("accurateCross", "totalCross"),
        "tackle_win_pct": ("wonTackle", "totalTackle"),
        "contest_win_pct": ("wonContest", "totalContest"),
        "aerial_win_pct": ("aerialWon", "aerialWon"),
    }
    for target, (num, den) in rate_pairs.items():
        if num in grouped.columns and den in grouped.columns:
            if target == "aerial_win_pct" and "aerialLost" in grouped.columns:
                denominator = grouped["aerialWon"] + grouped["aerialLost"]
            else:
                denominator = grouped[den]
            grouped[target] = grouped[num] / denominator.replace(0, np.nan) * 100

    rename = {}
    for column in grouped.columns:
        if column not in group_cols:
            rename[column] = f"match_{column}"
    return grouped.rename(columns=rename)


def prepare_understat(raw_dir: Path) -> pd.DataFrame:
    df = read_parquets(raw_dir, "understat__*.parquet")
    if df.empty:
        return df

    df = df.rename(columns={
        "player": "player_name",
        "us_team": "team_name",
        "league": "competition",
        "id": "understat_id",
    })
    df["competition"] = df["competition"].map(canonicalise_competition)
    df["team_name"] = df["team_name"].map(canonicalise_team)
    df["name_norm"] = df["player_name"].map(normalise_text)
    df["team_norm"] = df["team_name"].map(normalise_text)

    rename = {}
    for column in df.columns:
        if column not in {
            "player_name", "team_name", "competition", "season",
            "name_norm", "team_norm", "understat_id", "_source_file"
        }:
            rename[column] = f"understat_{column}"
    return df.rename(columns=rename)


def prepare_transfermarkt(raw_dir: Path) -> pd.DataFrame:
    df = read_parquets(raw_dir, "transfermarkt__*.parquet")
    if df.empty:
        return df

    df = df.rename(columns={
        "tm_name": "player_name",
        "team": "team_name",
        "league": "competition",
    })
    df["competition"] = df["competition"].map(canonicalise_competition)
    df["team_name"] = df["team_name"].map(canonicalise_team)
    df["name_norm"] = df["player_name"].map(normalise_text)
    df["team_norm"] = df["team_name"].map(normalise_text)
    df["dob_parsed"] = pd.to_datetime(df.get("dob"), errors="coerce")
    df["player_id_base"] = [
        stable_player_id(name, dob.strftime("%Y-%m-%d") if pd.notna(dob) else None)
        for name, dob in zip(df["player_name"], df["dob_parsed"])
    ]

    rename = {}
    for column in df.columns:
        if column not in {
            "player_name", "team_name", "competition", "season", "name_norm",
            "team_norm", "tm_id", "dob_parsed", "player_id_base", "_source_file"
        }:
            rename[column] = f"tm_{column}"
    return df.rename(columns=rename)


def prepare_clubelo(raw_dir: Path) -> pd.DataFrame:
    df = read_parquets(raw_dir, "clubelo__global__*.parquet")
    if df.empty:
        return df

    df = safe_numeric(df, ["elo", "rank", "level"])
    df["team_name"] = df["club"].map(canonicalise_team)
    df["team_norm"] = df["team_name"].map(normalise_text)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")

    # Latest available snapshot per club.
    df = df.sort_values("snapshot_date").drop_duplicates("team_norm", keep="last")
    return df[[
        c for c in ["team_name", "team_norm", "elo", "rank", "level", "country", "snapshot_date", "_source_file"]
        if c in df.columns
    ]].rename(columns={
        "elo": "clubelo_elo",
        "rank": "clubelo_rank",
        "level": "clubelo_level",
        "country": "clubelo_country",
        "snapshot_date": "clubelo_snapshot_date",
        "_source_file": "clubelo_source_file",
    })


# ---------- Matching ----------

@dataclass
class MatchResult:
    matched: pd.DataFrame
    audit: pd.DataFrame
    review: pd.DataFrame


def exact_join(base: pd.DataFrame, other: pd.DataFrame, source_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if other.empty:
        audit = pd.DataFrame([{
            "source": source_name,
            "method": "source_missing",
            "matched_rows": 0,
            "base_rows": len(base),
            "match_rate": 0.0,
        }])
        return base, audit, pd.DataFrame()

    base = base.copy()
    other = other.copy()
    base["_merge_key"] = make_match_key(base, "player_name", "team_name", "competition", "season")
    other["_merge_key"] = make_match_key(other, "player_name", "team_name", "competition", "season")

    # Avoid one-to-many explosions by keeping the most complete source row per key.
    source_payload = [c for c in other.columns if c not in {"_merge_key"}]
    other["_completeness"] = other[source_payload].notna().sum(axis=1)
    other = other.sort_values("_completeness", ascending=False).drop_duplicates("_merge_key")
    other = other.drop(columns=["_completeness"])

    payload = [
        c for c in other.columns
        if c not in {"player_name", "team_name", "competition", "season", "name_norm", "team_norm", "_merge_key"}
    ]
    merged = base.merge(other[["_merge_key"] + payload], on="_merge_key", how="left")
    marker = payload[0] if payload else None
    matched_mask = merged[marker].notna() if marker else pd.Series(False, index=merged.index)

    audit = pd.DataFrame([{
        "source": source_name,
        "method": "exact_name_team_league_season",
        "matched_rows": int(matched_mask.sum()),
        "base_rows": len(base),
        "match_rate": round(float(matched_mask.mean() * 100), 2),
    }])

    unmatched = merged.loc[~matched_mask, [
        c for c in ["player_name", "team_name", "competition", "season", "_merge_key"] if c in merged.columns
    ]].copy()
    unmatched["source"] = source_name

    return merged.drop(columns=["_merge_key"]), audit, unmatched


def fuzzy_fill(
    base: pd.DataFrame,
    source: pd.DataFrame,
    source_name: str,
    threshold: int = 92,
    review_threshold: int = 84,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Conservative fuzzy fill: only compares rows within the same league and season,
    gives a strong bonus for the same team, and never overwrites populated values.
    """
    if source.empty:
        return base, pd.DataFrame(), pd.DataFrame()

    result = base.copy()
    source = source.copy()

    identity_payload = {
        "sofascore_match": "match_player_id",
        "understat": "understat_id",
        "transfermarkt": "tm_id",
    }
    marker = identity_payload.get(source_name)
    if marker not in source.columns:
        marker = next((c for c in source.columns if c.endswith("_id") or c.endswith("id")), None)
    if marker is None:
        return result, pd.DataFrame(), pd.DataFrame()

    payload = [
        c for c in source.columns
        if c not in {"player_name", "team_name", "competition", "season", "name_norm", "team_norm"}
    ]

    matched_rows = []
    review_rows = []

    source_groups = {
        key: grp.reset_index(drop=True)
        for key, grp in source.groupby(["competition", "season"], dropna=False)
    }

    for idx, row in result.iterrows():
        # Skip rows already carrying this source marker.
        if marker in result.columns and pd.notna(row.get(marker)):
            continue

        group = source_groups.get((row.get("competition"), row.get("season")))
        if group is None or group.empty:
            continue

        same_team = group[group["team_norm"] == normalise_text(row.get("team_name"))]
        candidates = same_team if not same_team.empty else group
        choices = candidates["name_norm"].fillna("").tolist()
        if not choices:
            continue

        best = process.extractOne(normalise_text(row.get("player_name")), choices, scorer=fuzz.WRatio)
        if not best:
            continue
        _, score, pos = best
        candidate = candidates.iloc[pos]
        team_exact = candidate.get("team_norm", "") == normalise_text(row.get("team_name"))
        adjusted = min(100, score + (5 if team_exact else 0))

        record = {
            "source": source_name,
            "base_player": row.get("player_name"),
            "base_team": row.get("team_name"),
            "candidate_player": candidate.get("player_name"),
            "candidate_team": candidate.get("team_name"),
            "competition": row.get("competition"),
            "season": row.get("season"),
            "name_score": score,
            "team_exact": team_exact,
            "adjusted_score": adjusted,
        }

        if adjusted >= threshold:
            for column in payload:
                if column not in result.columns:
                    # Preserve the source column type. Initialising every new
                    # column with np.nan forces float64 and breaks when text
                    # values such as source filenames are assigned later.
                    source_dtype = source[column].dtype if column in source.columns else object
                    if pd.api.types.is_numeric_dtype(source_dtype):
                        result[column] = pd.Series(np.nan, index=result.index, dtype="float64")
                    elif pd.api.types.is_datetime64_any_dtype(source_dtype):
                        result[column] = pd.Series(pd.NaT, index=result.index, dtype="datetime64[ns]")
                    elif pd.api.types.is_bool_dtype(source_dtype):
                        result[column] = pd.Series(pd.NA, index=result.index, dtype="boolean")
                    else:
                        result[column] = pd.Series(pd.NA, index=result.index, dtype="object")

                if pd.isna(result.at[idx, column]) and column in candidate.index:
                    value = candidate[column]
                    if (
                        not pd.isna(value)
                        and pd.api.types.is_numeric_dtype(result[column].dtype)
                        and not isinstance(value, (int, float, np.integer, np.floating))
                    ):
                        result[column] = result[column].astype("object")
                    result.at[idx, column] = value
            matched_rows.append(record)
        elif adjusted >= review_threshold:
            review_rows.append(record)

    audit = pd.DataFrame([{
        "source": source_name,
        "method": "conservative_fuzzy",
        "matched_rows": len(matched_rows),
        "base_rows": len(base),
        "match_rate": round(len(matched_rows) / len(base) * 100, 2) if len(base) else 0,
    }])
    return result, audit, pd.DataFrame(review_rows)


# ---------- Master build ----------

def choose_base(sofa: pd.DataFrame, match: pd.DataFrame, understat: pd.DataFrame, tm: pd.DataFrame) -> pd.DataFrame:
    if not sofa.empty:
        base = sofa.copy()
        base["base_source"] = "sofascore_season"
        return base
    if not match.empty:
        base = match.copy()
        base["base_source"] = "sofascore_match_aggregate"
        return base
    if not understat.empty:
        base = understat.copy()
        base["base_source"] = "understat"
        return base
    if not tm.empty:
        base = tm.copy()
        base["base_source"] = "transfermarkt"
        return base
    raise RuntimeError("No usable player-season source was found.")


def add_master_fields(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()

    # Metadata coalescing.
    result["date_of_birth"] = pd.to_datetime(
        result.get("dob_parsed", pd.Series(pd.NaT, index=result.index)),
        errors="coerce",
    )
    if "match_dateOfBirthTimestamp" in result.columns:
        match_dob = pd.to_datetime(result["match_dateOfBirthTimestamp"], unit="s", errors="coerce")
        result["date_of_birth"] = result["date_of_birth"].fillna(match_dob)

    result["height_m"] = pd.to_numeric(result.get("tm_height_m"), errors="coerce")
    if "match_height" in result.columns:
        match_height_m = pd.to_numeric(result["match_height"], errors="coerce") / 100
        result["height_m"] = result["height_m"].fillna(match_height_m)

    result["position"] = result.get("tm_tm_position")
    if "match_position" in result.columns:
        result["position"] = result["position"].fillna(result["match_position"])

    result["market_value_eur"] = pd.to_numeric(result.get("tm_market_value_eur"), errors="coerce")
    if "match_proposedMarketValueRaw" in result.columns:
        def parse_value(value):
            if pd.isna(value):
                return np.nan
            try:
                parsed = json.loads(value) if isinstance(value, str) else value
                return float(parsed.get("value")) if isinstance(parsed, dict) else np.nan
            except Exception:
                return np.nan
        result["market_value_eur"] = result["market_value_eur"].fillna(
            result["match_proposedMarketValueRaw"].map(parse_value)
        )

    result["player_id"] = [
        stable_player_id(name, dob.strftime("%Y-%m-%d") if pd.notna(dob) else None)
        for name, dob in zip(result["player_name"], result["date_of_birth"])
    ]
    result["player_season_id"] = [
        hashlib.sha1(
            f"{pid}|{normalise_text(team)}|{normalise_text(comp)}|{season}".encode("utf-8")
        ).hexdigest()[:20]
        for pid, team, comp, season in zip(
            result["player_id"], result["team_name"], result["competition"], result["season"]
        )
    ]

    result["season_start_year"] = result["season"].map(season_start_year)

    # Master minutes/appearances.
    minutes_candidates = [
        c for c in ["sofa_minutes", "match_minutesPlayed", "understat_us_minutes"] if c in result.columns
    ]
    result["minutes"] = np.nan
    for column in minutes_candidates:
        result["minutes"] = result["minutes"].fillna(pd.to_numeric(result[column], errors="coerce"))

    appearances_candidates = [
        c for c in ["sofa_games", "match_match_appearances", "understat_us_games"] if c in result.columns
    ]
    result["appearances"] = np.nan
    for column in appearances_candidates:
        result["appearances"] = result["appearances"].fillna(pd.to_numeric(result[column], errors="coerce"))

    result["nineties"] = result["minutes"] / 90

    # Source coverage flags.
    result["has_sofascore_season"] = result.get("sofascore_id", pd.Series(np.nan, index=result.index)).notna()
    result["has_sofascore_match"] = result.get("match_player_id", pd.Series(np.nan, index=result.index)).notna()
    result["has_understat"] = result.get("understat_id", pd.Series(np.nan, index=result.index)).notna()
    result["has_transfermarkt"] = result.get("tm_id", pd.Series(np.nan, index=result.index)).notna()
    result["has_clubelo"] = result.get("clubelo_elo", pd.Series(np.nan, index=result.index)).notna()
    result["source_count"] = result[
        ["has_sofascore_season", "has_sofascore_match", "has_understat", "has_transfermarkt", "has_clubelo"]
    ].sum(axis=1)

    return result


def add_per90_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    nineties = result["nineties"].replace(0, np.nan)

    total_like = [
        c for c in result.columns
        if (
            c.startswith("match_")
            and pd.api.types.is_numeric_dtype(result[c])
            and not c.endswith("_pct")
            and c not in {
                "match_player_id", "match_height", "match_dateOfBirthTimestamp",
                "match_match_weighted_rating", "match_match_appearances"
            }
        )
    ]
    for column in total_like:
        result[f"{column}_per90"] = result[column] / nineties

    return result


def validate_master(frame: pd.DataFrame) -> pd.DataFrame:
    checks = []

    def add(name, failures, detail):
        checks.append({
            "check": name,
            "status": "PASS" if failures == 0 else "FAIL",
            "failure_rows": int(failures),
            "detail": detail,
        })

    add("player_season_id_unique", frame["player_season_id"].duplicated().sum(), "One row per player-team-competition-season.")
    add("player_name_present", frame["player_name"].isna().sum(), "Player name must be populated.")
    add("team_present", frame["team_name"].isna().sum(), "Team must be populated.")
    add("competition_present", frame["competition"].isna().sum(), "Competition must be populated.")
    add("season_present", frame["season"].isna().sum(), "Season must be populated.")
    add("minutes_non_negative", (pd.to_numeric(frame["minutes"], errors="coerce") < 0).sum(), "Minutes cannot be negative.")
    add("height_plausible", (
        frame["height_m"].notna() & ~frame["height_m"].between(1.45, 2.20)
    ).sum(), "Height expected between 1.45m and 2.20m.")
    add("market_value_non_negative", (
        frame["market_value_eur"].notna() & (frame["market_value_eur"] < 0)
    ).sum(), "Market value cannot be negative.")
    return pd.DataFrame(checks)


def build_master(
    raw_dir: Path,
    output_dir: Path,
    report_dir: Path,
    seasons: list[str] | None = None,
    competitions: list[str] | None = None,
    min_match_minutes: int = 1,
    fuzzy_threshold: int = 92,
    fuzzy_review_threshold: int = 84,
    write_csv: bool = True,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    print("Loading and preparing source tables...")
    sofa = prepare_sofascore_season(raw_dir)
    match = prepare_sofascore_match_aggregates(raw_dir, min_match_minutes)
    understat = prepare_understat(raw_dir)
    tm = prepare_transfermarkt(raw_dir)
    elo = prepare_clubelo(raw_dir)

    def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df.copy()
        if seasons and "season" in out.columns:
            out = out[out["season"].astype(str).isin(seasons)]
        if competitions and "competition" in out.columns:
            out = out[out["competition"].isin(competitions)]
        return out.reset_index(drop=True)

    sofa, match, understat, tm = map(apply_filters, [sofa, match, understat, tm])

    source_stats = pd.DataFrame([
        {"source": "sofascore_season", "rows": len(sofa), "columns": len(sofa.columns)},
        {"source": "sofascore_match_aggregate", "rows": len(match), "columns": len(match.columns)},
        {"source": "understat", "rows": len(understat), "columns": len(understat.columns)},
        {"source": "transfermarkt", "rows": len(tm), "columns": len(tm.columns)},
        {"source": "clubelo", "rows": len(elo), "columns": len(elo.columns)},
    ])

    master = choose_base(sofa, match, understat, tm)
    audits = []
    unmatched_reports = []
    fuzzy_reviews = []

    for source, source_name in [
        (match, "sofascore_match"),
        (understat, "understat"),
        (tm, "transfermarkt"),
    ]:
        master, audit, unmatched = exact_join(master, source, source_name)
        audits.append(audit)
        unmatched_reports.append(unmatched)

        master, fuzzy_audit, review = fuzzy_fill(
            master, source, source_name,
            threshold=fuzzy_threshold,
            review_threshold=fuzzy_review_threshold,
        )
        if not fuzzy_audit.empty:
            audits.append(fuzzy_audit)
        if not review.empty:
            fuzzy_reviews.append(review)

    # Team context merge.
    if not elo.empty:
        master["team_norm"] = master["team_name"].map(normalise_text)
        master = master.merge(elo.drop(columns=["team_name"], errors="ignore"), on="team_norm", how="left")

    master = add_master_fields(master)
    master = add_per90_metrics(master)

    # Ensure deterministic ordering and remove accidental exact duplicates.
    master = master.sort_values(
        ["season", "competition", "team_name", "player_name"],
        kind="stable"
    ).drop_duplicates("player_season_id", keep="first").reset_index(drop=True)

    validation = validate_master(master)
    coverage = pd.DataFrame({
        "metric": [
            "rows", "unique_players", "competitions", "seasons",
            "with_sofascore_season", "with_sofascore_match", "with_understat",
            "with_transfermarkt", "with_clubelo", "with_height", "with_market_value",
            "average_source_count"
        ],
        "value": [
            len(master),
            master["player_id"].nunique(),
            master["competition"].nunique(),
            master["season"].nunique(),
            int(master["has_sofascore_season"].sum()),
            int(master["has_sofascore_match"].sum()),
            int(master["has_understat"].sum()),
            int(master["has_transfermarkt"].sum()),
            int(master["has_clubelo"].sum()),
            int(master["height_m"].notna().sum()),
            int(master["market_value_eur"].notna().sum()),
            round(float(master["source_count"].mean()), 3),
        ],
    })

    paths = {}
    pq = output_dir / "master_player_dataset_v1.parquet"
    master.to_parquet(pq, index=False)
    paths["master_parquet"] = pq

    if write_csv:
        csv = output_dir / "master_player_dataset_v1.csv"
        master.to_csv(csv, index=False)
        paths["master_csv"] = csv

    source_stats.to_csv(report_dir / "source_input_summary.csv", index=False)
    pd.concat(audits, ignore_index=True).to_csv(report_dir / "merge_audit.csv", index=False)
    pd.concat(unmatched_reports, ignore_index=True).drop_duplicates().to_csv(
        report_dir / "unmatched_exact_rows.csv", index=False
    )
    if fuzzy_reviews:
        pd.concat(fuzzy_reviews, ignore_index=True).to_csv(
            report_dir / "fuzzy_matches_for_review.csv", index=False
        )
    else:
        pd.DataFrame(columns=[
            "source", "base_player", "base_team", "candidate_player", "candidate_team",
            "competition", "season", "name_score", "team_exact", "adjusted_score"
        ]).to_csv(report_dir / "fuzzy_matches_for_review.csv", index=False)

    validation.to_csv(report_dir / "master_validation.csv", index=False)
    coverage.to_csv(report_dir / "master_coverage_summary.csv", index=False)

    # Column dictionary.
    dictionary = pd.DataFrame({
        "column": master.columns,
        "dtype": [str(master[c].dtype) for c in master.columns],
        "non_null_rows": [int(master[c].notna().sum()) for c in master.columns],
        "coverage_pct": [round(float(master[c].notna().mean() * 100), 2) for c in master.columns],
    })
    dictionary.to_csv(report_dir / "master_column_dictionary.csv", index=False)

    return paths
