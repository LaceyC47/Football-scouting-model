# Data Source Audit — v0.1

## Decision

The project will use a **multi-source architecture**. No currently available free source provides
complete, current, broad player coverage together with event-level defending, progression,
possession security, contracts and market information.

Each source will therefore have a tightly defined role.

## Source matrix

| Source | Intended use | Strengths | Limitations | Status |
|---|---|---|---|---|
| Existing 2025/26 player CSV | Baseline current-season player pool, minutes and standard actions | Broad coverage; already obtained; easy to process | Only 102 columns; lacks many advanced possession and progression fields | Use now |
| football-data.org | Competitions, teams, squads, fixtures and identity cross-checking | Documented API; machine-readable; free top competitions | Not a rich recruitment-statistics source | Use |
| Understat | xG, xA, non-penalty xG, shot and attacking-chain context | Current top-European-league attacking data | Limited league coverage; little direct value for defensive midfield defending | Optional enrichment |
| StatsBomb Open Data | Event-data methodology, feature engineering and historical validation | Detailed events, lineups and selected 360 data | Selected competitions/seasons only; not a complete current transfer market | Validation/training only |
| Kaggle Transfermarkt-derived dataset | Player identity, club history, appearances, transfers and market-value proxies | Structured and regularly refreshed dataset | Third-party dataset; fields and refresh reliability must be audited; direct scraping avoided | Use cautiously |
| Official club/league sources | Current squad status, injuries, contract announcements and transfers | Strongest source for confirmed status changes | Not standardised; manual verification required | Verification layer |
| Manual scouting notes | Role, tactical fit, press behaviour and model exceptions | Captures qualities public aggregate data misses | Subjective and labour-intensive | Shortlisted players only |

## Explicit exclusions

### Direct Transfermarkt scraping

The pipeline will not depend on automated direct scraping of Transfermarkt. Its terms restrict
automated reproduction and scraping creates legal, stability and maintenance risks. We may use a
structured third-party dataset where its licence permits, while recording provenance and avoiding
redistribution of restricted raw material.

### StatsBomb Open Data as the master current database

StatsBomb Open Data is excellent event data, but it covers selected competitions and seasons.
It will be used to design and test features—not as evidence that every current transfer target
has been evaluated.

### Understat as a complete scouting source

Understat is primarily an expected-goals source covering the major European leagues. It can enrich
attacking evaluation, but cannot independently measure the defensive-midfielder profile.

## Collection strategy

1. Load the existing broad player CSV.
2. Standardise player, team, competition, season and position identifiers.
3. Add football-data.org identifiers and squad/fixture context.
4. Add permitted market/transfer fields from a structured third-party dataset.
5. Add Understat attacking fields only where matching confidence is high.
6. Calculate transparent proxy features from fields that genuinely exist.
7. Mark every unavailable feature as unavailable—never silently replace it.
8. Manually verify injuries, transfers, contracts and role for final shortlists.
9. Use historical StatsBomb event data to test whether proxy metrics behave sensibly.

## Data-quality rules

- Every field records its source.
- Raw files are never manually changed.
- Player matches receive a confidence score.
- Missing values remain missing unless an explicit, documented imputation rule exists.
- Scores are withheld when required components are missing.
- Current status claims require a dated source.
- Model rankings are screening tools, not substitutes for video scouting.

## Immediate conclusion

A useful free model is feasible, but the first version should be described as a **screening and
shortlisting model**, not a professional event-data replacement.
