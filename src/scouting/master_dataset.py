from __future__ import annotations
from pathlib import Path
import hashlib, re, unicodedata
import numpy as np
import pandas as pd

CANONICAL_METADATA = ("Rk","Player","Nation","Pos","Squad","Comp","Age","Born","MP","Starts","Min","90s")
PER90_COUNT_FIELDS = ("Gls","Ast","G+A","G-PK","PK","PKatt","Sh","SoT","TklW","Int","Fls","Fld","Off","Crs","OG","CrdY","CrdR","2CrdY")

def load_source(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx",".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")

def _clean_text(value):
    if pd.isna(value):
        return np.nan
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else np.nan

def _key(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def reconcile_metadata(frame):
    result = frame.copy()
    log = []
    for field in CANONICAL_METADATA:
        sources = [c for c in result.columns if c == field or c.startswith(f"{field}_stats_")]
        if not sources:
            continue
        merged = result[sources[0]].copy()
        for source in sources[1:]:
            merged = merged.combine_first(result[source])
        before = int(result[field].isna().sum()) if field in result else len(result)
        result[field] = merged
        log.append({"step":"reconcile_metadata","field":field,"source_columns":" | ".join(sources),
                    "rows_affected":max(0,before-int(merged.isna().sum()))})
    return result, log

def standardise_text(frame):
    result = frame.copy()
    log = []
    for col in ["Player","Nation","Pos","Squad","Comp"]:
        if col in result:
            before = result[col].copy()
            result[col] = result[col].map(_clean_text)
            log.append({"step":"standardise_text","field":col,"source_columns":col,
                        "rows_affected":int((before.fillna("") != result[col].fillna("")).sum())})
    return result, log

def convert_numeric(frame):
    result = frame.copy()
    log = []
    protected = {"Player","Nation","Pos","Squad","Comp"}
    for col in result.columns:
        if col in protected or pd.api.types.is_numeric_dtype(result[col]):
            continue
        source = result[col]
        cleaned = source.astype("string").str.replace(",","",regex=False).str.replace("%","",regex=False).str.strip()
        converted = pd.to_numeric(cleaned, errors="coerce")
        non_null = int(source.notna().sum())
        rate = float(converted.notna().sum()/non_null) if non_null else 0
        if rate >= 0.90:
            result[col] = converted
            log.append({"step":"convert_numeric","field":col,"source_columns":col,
                        "rows_affected":int(converted.notna().sum())})
    return result, log

def add_position_fields(frame):
    result = frame.copy()
    pos = result["Pos"].fillna("").astype(str)
    tokens = pos.map(lambda v: tuple(x.strip().upper() for x in v.split(",") if x.strip()))
    result["position_primary"] = tokens.map(lambda x: x[0] if x else np.nan)
    result["position_group"] = tokens.map(
        lambda x: "Goalkeeper" if "GK" in x else
                  "Midfielder" if "MF" in x else
                  "Defender" if "DF" in x else
                  "Forward" if "FW" in x else "Unknown"
    )
    result["is_goalkeeper"] = tokens.map(lambda x: "GK" in x)
    result["is_defender"] = tokens.map(lambda x: "DF" in x)
    result["is_midfielder"] = tokens.map(lambda x: "MF" in x)
    result["is_forward"] = tokens.map(lambda x: "FW" in x)
    result["is_pure_midfielder"] = tokens.map(lambda x: set(x) == {"MF"})
    result["is_mixed_position"] = tokens.map(lambda x: len(set(x)) > 1)
    return result, [{"step":"derive_positions","field":"position_*","source_columns":"Pos","rows_affected":len(result)}]

def add_ids(frame, season):
    result = frame.copy()
    result["season"] = season
    born = pd.to_numeric(result["Born"], errors="coerce").fillna(-1).astype(int).astype(str)
    identity = result["Player"].map(_key) + "|" + born
    result["player_id"] = identity.map(lambda x: hashlib.sha1(x.encode()).hexdigest()[:16])
    base = (result["player_id"] + "|" + result["Squad"].map(_key) + "|" +
            result["Comp"].map(_key) + "|" + season).map(lambda x: hashlib.sha1(x.encode()).hexdigest()[:20])
    occurrence = base.groupby(base).cumcount()
    result["player_season_id"] = np.where(occurrence.eq(0), base, base + "-" + occurrence.astype(str))
    return result, [{"step":"create_ids","field":"player_id | player_season_id",
                     "source_columns":"Player | Born | Squad | Comp | season","rows_affected":len(result)}]

def add_derived_metrics(frame):
    result = frame.copy()
    nineties = pd.to_numeric(result["90s"], errors="coerce")
    created = []
    for field in PER90_COUNT_FIELDS:
        if field in result:
            result[f"{field}_per90_derived"] = np.where(nineties > 0, pd.to_numeric(result[field], errors="coerce")/nineties, np.nan)
            created.append(f"{field}_per90_derived")
    result["minutes_band"] = pd.cut(pd.to_numeric(result["Min"], errors="coerce"),
        [-np.inf,0,449,899,1499,np.inf],
        labels=["none","under_450","450_899","900_1499","1500_plus"])
    created.append("minutes_band")
    return result, [{"step":"derive_metrics","field":" | ".join(created),
                     "source_columns":"90s and count fields","rows_affected":len(result)}]

def validate_master(frame, required_columns, age_bounds=(15,45), minutes_tolerance=95):
    checks = []
    def add(name, failures, detail):
        checks.append({"check":name,"status":"PASS" if failures == 0 else "FAIL",
                       "failure_rows":int(failures),"detail":detail})
    missing = [c for c in required_columns if c not in frame]
    add("required_columns_present", len(missing), "Missing: " + ", ".join(missing) if missing else "All present")
    add("player_season_id_unique", int(frame["player_season_id"].duplicated().sum()), "IDs must be unique")
    age = pd.to_numeric(frame["Age"], errors="coerce")
    add("age_within_bounds", int((age.notna() & ~age.between(*age_bounds)).sum()), f"Expected {age_bounds[0]}-{age_bounds[1]}")
    minutes = pd.to_numeric(frame["Min"], errors="coerce")
    nineties = pd.to_numeric(frame["90s"], errors="coerce")
    add("minutes_consistent_with_90s", int((minutes.notna() & nineties.notna() & (minutes-nineties*90).abs().gt(minutes_tolerance)).sum()),
        f"Tolerance {minutes_tolerance} minutes")
    add("minutes_non_negative", int((minutes.notna() & minutes.lt(0)).sum()), "Minutes cannot be negative")
    missing_identity = frame[["Player","Squad","Comp","Pos"]].isna().any(axis=1)
    add("core_identity_complete", int(missing_identity.sum()), "Player, squad, competition and position required")
    return pd.DataFrame(checks)

def build_master_dataset(source_path, output_path, season="2025-2026",
                         required_columns=None, age_bounds=(15,45),
                         minutes_tolerance=95, drop_exact_duplicate_rows=True):
    source = load_source(source_path)
    work = source.copy()
    logs = []
    if drop_exact_duplicate_rows:
        before = len(work)
        work = work.drop_duplicates().reset_index(drop=True)
        logs.append({"step":"drop_exact_duplicates","field":"all_columns","source_columns":"all_columns",
                     "rows_affected":before-len(work)})
    for fn in (reconcile_metadata, standardise_text, convert_numeric, add_position_fields):
        work, step = fn(work); logs.extend(step)
    work, step = add_ids(work, season); logs.extend(step)
    work, step = add_derived_metrics(work); logs.extend(step)

    priority = ["player_season_id","player_id","season","Player","Nation","Pos","position_primary","position_group",
                "is_goalkeeper","is_defender","is_midfielder","is_forward","is_pure_midfielder","is_mixed_position",
                "Squad","Comp","Age","Born","MP","Starts","Min","90s","minutes_band"]
    order = [c for c in priority if c in work] + [c for c in work if c not in priority]
    work = work[order]

    validation = validate_master(work, required_columns or ["Player","Squad","Comp","Pos","Age","Min","90s"],
                                 age_bounds, minutes_tolerance)
    summary = pd.DataFrame([
        ("source_rows",len(source)),("source_columns",len(source.columns)),
        ("master_rows",len(work)),("master_columns",len(work.columns)),
        ("exact_duplicate_rows_removed",len(source)-len(work)),
        ("unique_players",work["player_id"].nunique()),
        ("unique_player_season_rows",work["player_season_id"].nunique()),
        ("competitions",work["Comp"].nunique()),("squads",work["Squad"].nunique()),
        ("midfielder_rows",int(work["is_midfielder"].sum())),
        ("pure_midfielder_rows",int(work["is_pure_midfielder"].sum()))
    ], columns=["metric","value"])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work.to_csv(output_path, index=False)
    return work, pd.DataFrame(logs), validation, summary
