import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scouting.cleaning import clean_player_data, snake_case


def test_snake_case():
    assert snake_case("TklW/90") == "tklw_per_90"
    assert snake_case("Player Name") == "player_name"


def test_clean_player_data_creates_ids_and_nineties():
    raw = pd.DataFrame({
        "Player": ["Test Player"],
        "Squad": ["Test Club"],
        "League": ["Test League"],
        "Minutes": [900],
    })
    aliases = {
        "player": ["player"],
        "club": ["squad"],
        "competition": ["league"],
        "minutes": ["minutes"],
    }

    cleaned = clean_player_data(raw, aliases, "2025-2026")

    assert cleaned.loc[0, "nineties"] == 10
    assert cleaned.loc[0, "data_quality_flag"] == "complete"
    assert len(cleaned.loc[0, "player_season_id"]) == 16
