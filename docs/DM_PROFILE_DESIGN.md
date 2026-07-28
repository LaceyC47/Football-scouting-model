# Defensive Midfielder Profile Design

## Project principle

The system is profile-specific, club-independent and purely statistical. It will not assign one
universal rating to every defensive midfielder.

## Intended profile family

### Ball-winning 6
Measures defensive activity and defensive efficiency.

### Holding/controller 6
Measures retention, distribution security and positional discipline.

### Progressive 6
Measures advancement through passing and carrying.

### Press-resistant 6
Measures retention and progression under pressure using available statistical proxies.

### Complete 6
A balanced profile composed from the other dimensions rather than an unexplained overall score.

## What Version 0 can measure

The current file supports a provisional defensive-activity view using:

- tackles won per 90
- interceptions per 90
- fouls per 90
- cards per 90
- minutes and starts as sample/reliability context

This must not be presented as the final DM model because tackles won and interceptions are
activity measures, not complete measures of defensive quality or positioning.

## Data still required

The next source expansion should prioritise:

- progressive passes and carries
- pass completion by distance
- passes into the final third
- miscontrols and dispossessions
- take-on attempts and success
- ball recoveries
- tackle attempts and success
- ground and aerial duel attempts and win rates
- pressures, pressure regains or suitable pressing proxies

## Scoring policy

Weights will only be set after the feature inventory is complete. Every profile score must show:

1. included metrics;
2. transformation and direction;
3. comparison population;
4. minimum-minute rule;
5. weight;
6. missing-data treatment.

Age, market value and club fit should remain filters or contextual outputs unless explicitly
included in a separate recruitment-value profile.
