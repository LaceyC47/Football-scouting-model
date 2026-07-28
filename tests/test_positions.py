from scouting.positions import parse_position

def test_pure_midfielder():
    flags = parse_position("MF")
    assert flags.is_midfielder
    assert flags.is_pure_midfielder
    assert not flags.is_mixed_midfielder

def test_mixed_midfielder():
    flags = parse_position("MF,FW")
    assert flags.is_midfielder
    assert flags.is_forward
    assert flags.is_mixed_midfielder
    assert not flags.is_pure_midfielder
