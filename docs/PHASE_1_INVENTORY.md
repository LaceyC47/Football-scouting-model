# Phase 1 — Dataset Inventory

This phase inventories every Parquet file collected by `football-data-mcp`.

## Outputs

The script creates:

- `reports/inventory/dataset_inventory.csv`
  - one row per file
  - source, competition, season, row count, column count, size, checksum and errors

- `reports/inventory/column_inventory.csv`
  - one row per file-column combination
  - column name, data type and source context

- `reports/inventory/column_frequency.csv`
  - how often each column appears
  - which source families contain it

- `reports/inventory/sample_rows.csv`
  - five sample rows per file, stored as JSON

- `reports/inventory/inventory_summary.csv`
  - overall counts

- `reports/inventory/source_summary.csv`
  - summary by source type

## Run

From the repository root:

```cmd
python scripts\run_inventory.py
```

The script only reads the downloaded Parquet files. It does not modify or delete them.
