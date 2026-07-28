# Master Player Database Schema — v0.1

One row represents one player in one club, competition and season.

## Keys and provenance

| Field | Type | Required | Description |
|---|---|---:|---|
| player_season_id | string | Yes | Internal stable row key |
| player_id | string | Yes | Internal player identity key |
| source_name | string | Yes | Primary source for the row |
| source_player_id | string | No | Player ID in the source |
| source_updated_at | datetime | No | Source refresh timestamp |
| match_confidence | decimal | Yes | Confidence in cross-source identity match |
| data_quality_flag | string | Yes | complete / partial / review |

## Identity

| Field | Type | Required |
|---|---|---:|
| player_name | string | Yes |
| known_as | string | No |
| date_of_birth | date | No |
| age_at_season_start | decimal | No |
| nationality | string | No |
| height_cm | integer | No |
| preferred_foot | category | No |

## Football context

| Field | Type | Required |
|---|---|---:|
| season | string | Yes |
| club | string | Yes |
| competition | string | Yes |
| country | string | Yes |
| primary_position | string | Yes |
| secondary_positions | string | No |
| role_classification | string | No |
| squad_status | string | No |

## Playing time

| Field | Type |
|---|---|
| appearances | integer |
| starts | integer |
| minutes | integer |
| full_90s | decimal |
| minutes_share | decimal |

## Raw performance fields

The pipeline stores raw totals where available before calculating per-90 values.

### Defending

- tackles
- tackles_won
- interceptions
- blocks
- clearances
- recoveries
- aerial_duels
- aerial_duels_won
- fouls_committed
- yellow_cards
- red_cards

### Passing and progression

- passes_attempted
- passes_completed
- progressive_passes
- passes_into_final_third
- long_passes_attempted
- long_passes_completed
- switches
- through_balls
- key_passes

### Possession and carrying

- touches
- carries
- progressive_carries
- successful_take_ons
- attempted_take_ons
- dispossessions
- miscontrols
- times_tackled
- passes_received

### Output

- goals
- assists
- xg
- npxg
- xa
- shots

## Availability and market

| Field | Type |
|---|---|
| contract_expiry | date |
| market_value_eur | decimal |
| estimated_fee_low_eur | decimal |
| estimated_fee_high_eur | decimal |
| injury_days_last_365 | integer |
| injury_days_last_3y | integer |
| current_injury | boolean |
| transfer_status | string |
| availability_source_date | date |

## Engineered features

All calculated features must have a formula in the model documentation.

- defensive_activity_per90
- defensive_efficiency
- foul_rate
- card_rate
- pass_completion_pct
- progressive_passes_per90
- progressive_carries_per90
- turnover_rate
- retention_proxy
- press_resistance_proxy
- progression_score
- defensive_solidity_score
- discipline_score
- athletic_proxy
- league_strength_factor
- age_curve_factor
- availability_score
- role_fit_score
- recruitment_score
- score_coverage_pct

## Missing-data policy

A field absent from a source remains null. A composite score must report `score_coverage_pct`.
Players below the minimum coverage threshold will appear in a review list rather than the main
ranking.
