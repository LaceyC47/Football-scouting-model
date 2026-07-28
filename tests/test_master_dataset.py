import pandas as pd
from scouting.master_dataset import reconcile_metadata, add_position_fields, add_ids, validate_master

def test_reconcile_metadata():
    frame = pd.DataFrame({"Player":["A"],"Pos":[None],"Pos_stats_misc":["MF"]})
    result, _ = reconcile_metadata(frame)
    assert result.loc[0,"Pos"] == "MF"

def test_position_fields():
    frame = pd.DataFrame({"Pos":["MF","MF,FW","DF"]})
    result, _ = add_position_fields(frame)
    assert result["is_pure_midfielder"].tolist() == [True,False,False]

def test_ids_unique():
    frame = pd.DataFrame({"Player":["A","A"],"Born":[2000,2000],"Squad":["Club","Club"],"Comp":["League","League"]})
    result, _ = add_ids(frame,"2025-2026")
    assert result["player_season_id"].is_unique

def test_valid_frame_passes():
    frame = pd.DataFrame({"Player":["A"],"Squad":["Club"],"Comp":["League"],"Pos":["MF"],
                          "Age":[24],"Min":[900],"90s":[10.0],"player_season_id":["abc"]})
    report = validate_master(frame,["Player","Squad","Comp","Pos","Age","Min","90s"])
    assert (report["status"] == "PASS").all()
