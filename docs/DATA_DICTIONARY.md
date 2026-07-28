# Data Dictionary

## Dataset

- File: `players_data-2025_2026.csv`
- Rows: **2,839**
- Columns: **102**
- Unique players: **2,687**
- Competitions: **5**
- Squads: **96**

The source is a merged season-level player table. It contains standard player metadata,
playing-time statistics, shooting, goalkeeper, team on/off, and miscellaneous defensive data.

## Important structural finding

The file repeats metadata columns for several source tables. Examples include `Nation`,
`Pos`, `Comp`, `Age`, `Born`, `Rk`, `90s`, and their suffixed versions such as
`Pos_stats_misc`. These are not separate football metrics and must not be treated as model
features without reconciliation.

See `reports/column_profile.csv` for the complete machine-readable dictionary and
`reports/duplicate_metadata_groups.csv` for repeated metadata groups.

## Metric coverage

Currently available DM-relevant fields include:

- `TklW`
- `Int`
- `Fls`
- `Fld`
- `CrdY`
- `CrdR`
- `Crs`
- `Off`

Per-90 versions of count fields are created by the audit code using the primary `90s` field.

## Current limitation

This dataset is not yet sufficient for a complete defensive-midfielder profile model. It lacks
the detailed passing, carrying, possession-security and duel-efficiency tables needed to
distinguish ball-winners, controllers and progressive midfielders reliably.
