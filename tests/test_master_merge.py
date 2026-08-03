import pandas as pd

from scouting.master_merge import (
    canonicalise_competition,
    canonicalise_team,
    normalise_text,
    stable_player_id,
    validate_master,
)


def test_normalise_text_handles_accents():
    assert normalise_text("João Palhinha") == "joao palhinha"


def test_team_alias():
    assert canonicalise_team("Man Utd") == "Manchester United"


def test_competition_alias():
    assert canonicalise_competition("Premier League") == "England Premier League"


def test_stable_player_id():
    assert stable_player_id("Player A", "2000-01-01") == stable_player_id("Player A", "2000-01-01")


def test_validation_valid_frame():
    frame = pd.DataFrame({
        "player_season_id": ["a"],
        "player_name": ["Player A"],
        "team_name": ["Club"],
        "competition": ["League"],
        "season": ["2025-2026"],
        "minutes": [900],
        "height_m": [1.85],
        "market_value_eur": [10_000_000],
    })
    report = validate_master(frame)
    assert (report["status"] == "PASS").all()


def test_exact_join_renames_generic_source_file():
    from scouting.master_merge import exact_join
    base = pd.DataFrame({
        "player_name": ["Player A"], "team_name": ["Club"],
        "competition": ["England Premier League"], "season": ["2025-2026"],
        "_source_file": ["base.parquet"],
    })
    other = pd.DataFrame({
        "player_name": ["Player A"], "team_name": ["Club"],
        "competition": ["England Premier League"], "season": ["2025-2026"],
        "understat_id": [123], "_source_file": ["understat.parquet"],
    })
    merged, _, _ = exact_join(base, other, "understat")
    assert "_source_file" in merged.columns
    assert "understat_source_file" in merged.columns
    assert merged.loc[0, "understat_source_file"] == "understat.parquet"
