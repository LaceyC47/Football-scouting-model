# Master Merge Engine v1

This engine builds one row per player-team-competition-season from the downloaded public data.

## Sources used

- SofaScore season player statistics — base table
- SofaScore match player statistics — aggregated to player-season
- Understat season data — xG, xA, xGChain and xGBuildup
- Transfermarkt — DOB, height, nationality, position, market value and contracts
- ClubElo — club-strength context

## Matching order

1. Exact player + team + competition + season
2. Conservative fuzzy matching within the same competition and season
3. Team agreement adds a score bonus
4. Borderline fuzzy matches are not merged automatically; they are written to:
   `reports/merge/fuzzy_matches_for_review.csv`

## Main output

`data/processed/master_player_dataset_v1.parquet`

A CSV copy is also created by default.

## Audit outputs

- `source_input_summary.csv`
- `merge_audit.csv`
- `unmatched_exact_rows.csv`
- `fuzzy_matches_for_review.csv`
- `master_validation.csv`
- `master_coverage_summary.csv`
- `master_column_dictionary.csv`

The engine preserves source-specific column prefixes so every metric remains traceable.
