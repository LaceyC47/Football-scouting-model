from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scouting.master_dataset import build_master_dataset

with open(ROOT / "config/master_dataset_config.json", encoding="utf-8") as f:
    config = json.load(f)

master, log, validation, summary = build_master_dataset(
    ROOT / config["input_file"],
    ROOT / config["output_file"],
    season=config["season"],
    required_columns=config["required_columns"],
    age_bounds=tuple(config["age_bounds"]),
    minutes_tolerance=config["minutes_tolerance"],
    drop_exact_duplicate_rows=config["drop_exact_duplicate_rows"]
)
reports = ROOT / "reports"
reports.mkdir(exist_ok=True)
log.to_csv(reports / "master_transformation_log.csv", index=False)
validation.to_csv(reports / "master_validation_report.csv", index=False)
summary.to_csv(reports / "master_dataset_summary.csv", index=False)
print("Master dataset built successfully.")
print(f"Rows: {len(master):,}")
print(f"Columns: {len(master.columns):,}")
print(f"Validation checks passed: {(validation.status == 'PASS').sum()}/{len(validation)}")
