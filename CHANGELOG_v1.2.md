# v1.2 Fix

- Fixed `pandas.errors.MergeError` caused by repeated generic `_source_file` columns.
- Each joined source now receives its own traceability column, such as:
  - `sofascore_match_source_file`
  - `understat_source_file`
  - `transfermarkt_source_file`
- Added a regression test covering the failure.
