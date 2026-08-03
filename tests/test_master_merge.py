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


def test_sofascore_match_id_is_recognised_in_master_coverage():
    from scouting.master_merge import add_master_fields

    frame = pd.DataFrame({
        "player_name": ["Player A"],
        "team_name": ["Club"],
        "competition": ["England Premier League"],
        "season": ["2025-2026"],
        "sofascore_id": [1],
        "match_player_id": [101],
        "sofa_minutes": [900],
    })

    result = add_master_fields(frame)

    assert bool(result.loc[0, "has_sofascore_match"]) is True
    assert result.loc[0, "source_count"] == 2


def test_exact_join_uses_match_player_id_as_marker():
    from scouting.master_merge import exact_join

    base = pd.DataFrame({
        "player_name": ["Player A"],
        "team_name": ["Club"],
        "competition": ["England Premier League"],
        "season": ["2025-2026"],
    })
    other = pd.DataFrame({
        "match_player_id": [101],
        "player_name": ["Player A"],
        "team_name": ["Club"],
        "competition": ["England Premier League"],
        "season": ["2025-2026"],
        "match_minutesPlayed": [900],
    })

    merged, audit, _ = exact_join(base, other, "sofascore_match")

    assert merged.loc[0, "match_player_id"] == 101
    assert audit.loc[0, "matched_rows"] == 1
