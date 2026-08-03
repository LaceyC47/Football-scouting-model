# Phase 1 GitHub Instructions

1. Download and extract `football-scouting-phase-1-inventory.zip`.
2. Open GitHub Desktop.
3. Select **Repository → Show in Explorer**.
4. Copy everything inside the extracted folder into the root of `Football-scouting-model`.
5. Choose **Merge folders** or **Replace files in the destination** when prompted.
6. In GitHub Desktop, commit with:

```text
Add Phase 1 parquet inventory
```

7. Click **Commit to main**.
8. Click **Push origin**.

## Run the inventory

Open Command Prompt in the repository folder and run:

```cmd
python scripts\run_inventory.py
```

When it finishes, upload these six files from:

```text
reports\inventory
```

- `dataset_inventory.csv`
- `column_inventory.csv`
- `column_frequency.csv`
- `sample_rows.csv`
- `inventory_summary.csv`
- `source_summary.csv`
