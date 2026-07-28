# Data Collection Pipeline — v0.1

## Pipeline stages

1. **Ingest**
   - Save each downloaded source unchanged in `data/raw/<source>/<date>/`.
   - Generate a file checksum and ingestion log.

2. **Standardise**
   - Convert column names to snake_case.
   - Standardise accents, whitespace, dates, clubs, competitions and positions.
   - Retain original text columns for auditability.

3. **Resolve identities**
   - Exact source-ID match where possible.
   - Otherwise use name, DOB, club and nationality.
   - Assign a match-confidence score.
   - Send uncertain matches to a review table.

4. **Build player-season table**
   - One record per player, club, competition and season.
   - Preserve loan and mid-season transfer spells separately.
   - Create aggregate season records only as a derived table.

5. **Engineer features**
   - Convert totals to per-90 only above a minimum-minutes rule.
   - Produce possession-adjusted metrics only when team possession is available.
   - Calculate percentiles within appropriate position and competition groups.

6. **Score**
   - Apply role-specific models.
   - Publish component scores, overall score and coverage percentage.
   - Never rank a player using an unavailable component as though it were zero.

7. **Validate**
   - Benchmark established players.
   - Inspect top-ranked outliers.
   - Compare results with video and written scouting.
   - Record every model adjustment in the changelog.

8. **Export**
   - Master parquet/CSV dataset.
   - Excel shortlist.
   - Data-quality report.
   - Player report cards.

## Refresh cadence

- Performance data: weekly during the season
- Transfers and squad status: before each published shortlist
- Market values: monthly or when the source refreshes
- Injuries: before each shortlist and major model review
- League-strength factors: once per season, with mid-season review

## First executable build

The first build will use the uploaded broad player CSV and only its genuinely available fields.
Its purpose is to establish identity cleaning, eligibility filters, per-90 calculations and data
quality reporting. Advanced DM scoring will remain disabled until sufficient components are present.
