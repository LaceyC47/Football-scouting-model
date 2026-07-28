import pandas as pd
from scouting.audit import build_dm_pool, build_column_profile

def test_dm_pool_filters_minutes_age_and_position():
    frame = pd.DataFrame({
        "Player": ["A", "B", "C", "D"],
        "Pos": ["MF", "MF,FW", "DF", "MF"],
        "Min": [1000, 1200, 2000, 500],
        "Age": [24, 22, 25, 21],
        "90s": [11.1, 13.3, 22.2, 5.6],
        "TklW": [10, 12, 20, 3],
        "Int": [8, 9, 15, 2],
    })
    broad, pure = build_dm_pool(frame, minimum_minutes=900)
    assert set(broad["Player"]) == {"A", "B"}
    assert set(pure["Player"]) == {"A"}

def test_column_profile_contains_missingness():
    frame = pd.DataFrame({"A": [1, None], "B": ["x", "y"]})
    profile = build_column_profile(frame)
    assert profile.loc[profile["column"] == "A", "missing"].iloc[0] == 1
