from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scouting.inventory import build_inventory


def main() -> int:
    config_path = ROOT / "config" / "inventory_config.json"
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    raw_dir = Path(config["raw_data_directory"])
    output_dir = ROOT / config["output_directory"]

    if not raw_dir.exists():
        print(f"ERROR: Raw data folder not found: {raw_dir}")
        return 1

    outputs = build_inventory(
        raw_dir=raw_dir,
        output_dir=output_dir,
        sample_rows=int(config.get("sample_rows_per_file", 5)),
    )

    print("\nPhase 1 inventory complete.")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
