# Master Dataset

`data/processed/master_players.csv` is now the canonical input for future scouting models.

## Build result

- Source rows: **2,839**
- Master rows: **2,839**
- Master columns: **132**
- Unique players: **2,690**
- Validation checks passed: **6/6**

## Transformations

- Reconciles repeated source metadata.
- Standardises core text fields.
- Converts numeric-looking columns.
- Adds position flags.
- Creates `player_id` and `player_season_id`.
- Creates available count-based per-90 metrics.
- Adds a minutes reliability band.
- Preserves source columns for traceability.

All later modelling code should read `data/processed/master_players.csv`, not the raw CSV.
