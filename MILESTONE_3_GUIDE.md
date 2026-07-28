# Milestone 3 Installation Guide

## Copy these folders into the repository root

- `config/`
- `docs/`
- `reports/`
- `scripts/`
- `src/`
- `tests/`

Allow Windows to merge folders. Do not copy the dataset from this ZIP; your existing file should
remain at:

`data/raw/players_data-2025_2026.csv`

## Run the audit

From the repository root:

```bash
python scripts/audit_dataset.py
```

Expected result:

```text
Milestone 3 audit completed successfully.
```

The script recreates all CSV files in `reports/`.

## Run tests

```bash
python -m pytest
```

## Suggested commit message

`Add Milestone 3 dataset audit and DM model foundation`
