# Data Quality Report

## Audit result

The dataset loaded successfully with **2,839 rows and 102 columns**.

## Coverage

- Unique player names: **2,687**
- Unique squads: **96**
- Unique competitions: **5**
- Broad midfield recruitment pool: **735**
- Pure-midfielder pool: **394**

The default recruitment audit uses ages **18–29** and at least **900 minutes**. A separate flag
shows which players have reached the preferred **1,500-minute** reliability threshold.

## Main issues

1. **Repeated metadata columns.** Merged FBref-style tables repeat identifiers and demographic
   fields. These must be reconciled rather than included as independent predictors.
2. **Goalkeeper-only sparsity.** Goalkeeping columns are naturally missing for outfield players.
   Missingness in those fields is structural, not necessarily bad data.
3. **Multiple rows for transferred players.** A player can appear for more than one club in the
   same competition season. Player name alone is therefore not a valid unique key.
4. **Limited DM feature breadth.** The miscellaneous table supplies defensive counts, but not
   enough passing, possession and carrying detail for a complete profile-specific model.
5. **Very small samples.** The raw file contains players with only a few minutes. They remain in
   the source audit but are excluded from the modelling pool through minimum-minute rules.

## Files to review

- `reports/dataset_summary.csv`
- `reports/column_profile.csv`
- `reports/duplicate_report.csv`
- `reports/duplicate_metadata_groups.csv`
- `reports/position_breakdown.csv`
- `reports/dm_pool_broad.csv`
- `reports/dm_pool_pure.csv`
