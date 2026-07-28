from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


def discover_input_files(raw_dir: Path) -> list[Path]:
    """Return supported data files from the raw-data directory."""
    if not raw_dir.exists():
        return []

    return sorted(
        path for path in raw_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith("~$")
    )


def read_table(path: Path, preferred_sheet: str | None = None) -> pd.DataFrame:
    """Read one CSV or Excel table and add basic source metadata."""
    suffix = path.suffix.lower()

    if suffix == ".csv":
        frame = pd.read_csv(path)
        sheet_name = None
    elif suffix in {".xlsx", ".xlsm"}:
        excel = pd.ExcelFile(path)
        sheet_name = preferred_sheet if preferred_sheet in excel.sheet_names else excel.sheet_names[0]
        frame = pd.read_excel(path, sheet_name=sheet_name)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    frame = frame.dropna(how="all").copy()
    frame["source_file"] = path.name
    frame["source_sheet"] = sheet_name
    return frame
