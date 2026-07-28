"""Position parsing utilities."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PositionFlags:
    raw: str
    tokens: tuple[str, ...]
    is_goalkeeper: bool
    is_defender: bool
    is_midfielder: bool
    is_forward: bool
    is_pure_midfielder: bool
    is_mixed_midfielder: bool


def parse_position(value: object) -> PositionFlags:
    raw = "" if value is None else str(value).strip()
    tokens = tuple(token.strip().upper() for token in raw.split(",") if token.strip())
    token_set = set(tokens)

    is_goalkeeper = "GK" in token_set
    is_defender = "DF" in token_set
    is_midfielder = "MF" in token_set
    is_forward = "FW" in token_set
    is_pure_midfielder = token_set == {"MF"}
    is_mixed_midfielder = is_midfielder and not is_pure_midfielder

    return PositionFlags(
        raw=raw,
        tokens=tokens,
        is_goalkeeper=is_goalkeeper,
        is_defender=is_defender,
        is_midfielder=is_midfielder,
        is_forward=is_forward,
        is_pure_midfielder=is_pure_midfielder,
        is_mixed_midfielder=is_mixed_midfielder,
    )


def add_position_flags(frame, position_column: str = "Pos"):
    result = frame.copy()
    flags = result[position_column].map(parse_position)
    result["position_tokens"] = flags.map(lambda x: ",".join(x.tokens))
    result["is_goalkeeper"] = flags.map(lambda x: x.is_goalkeeper)
    result["is_defender"] = flags.map(lambda x: x.is_defender)
    result["is_midfielder"] = flags.map(lambda x: x.is_midfielder)
    result["is_forward"] = flags.map(lambda x: x.is_forward)
    result["is_pure_midfielder"] = flags.map(lambda x: x.is_pure_midfielder)
    result["is_mixed_midfielder"] = flags.map(lambda x: x.is_mixed_midfielder)
    return result
