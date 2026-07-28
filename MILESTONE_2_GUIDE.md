# Milestone 2 — Baseline Data Pipeline

This milestone adds the first executable version of the project.

## What it does

- Finds CSV and Excel files in `data/raw`
- Uses the configured Excel sheet when available
- Standardises column names
- Maps common source labels to canonical labels
- Cleans player, club, competition and position text
- Converts key numeric fields safely
- Creates stable internal player and player-season IDs
- Produces a master player-season CSV
- Produces a column-level data-quality report
- Produces a table of records requiring manual review
- Records files that failed during ingestion
- Includes automated tests

## Project structure

```text
config/
    pipeline.yml
data/
    raw/
        sample_players.csv
    processed/
    exports/
models/
notebooks/
scripts/
    profile_dataset.py
    run_pipeline.py
src/
    scouting/
tests/
requirements.txt
```

## First setup on Windows

Open the repository in GitHub Desktop and click **Repository → Open in
Command Prompt**. Then run:

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

## Test the included sample

```bash
py scripts/run_pipeline.py
```

The pipeline should create:

- `data/processed/master_player_seasons.csv`
- `data/exports/data_quality_report.csv`
- `data/exports/rows_for_review.csv`
- `data/exports/ingestion_failures.csv`

Run the automated tests with:

```bash
py -m pytest
```

## Use the real dataset

1. Delete `data/raw/sample_players.csv`.
2. Copy the real CSV or Excel workbook into `data/raw`.
3. Run:

```bash
py scripts/run_pipeline.py
```

The pipeline currently prioritises the Excel sheet `Pure MF Pool` when that sheet
exists. This can be changed in `config/pipeline.yml`.

## Important limitation

This is the database foundation, not the final recruitment model. It does not yet
pretend to calculate progression, press resistance or athleticism when the required
source fields are unavailable.
