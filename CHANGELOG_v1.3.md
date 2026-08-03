# v1.3 Fix

- Fixed SofaScore match coverage incorrectly reporting zero.
- The SofaScore source player ID is retained as `match_player_id`.
- The master `player_id` no longer overwrites the SofaScore match ID.
- Exact merge audits now use explicit source identifiers.
- Added regression tests for SofaScore match coverage and audit counting.

Transfermarkt coverage remains limited because the original collector was
interrupted before every competition was downloaded. This version reports that
honestly rather than treating absent source files as failed matches.
