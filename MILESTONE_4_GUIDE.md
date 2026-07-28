# Milestone 4 GitHub Guide

1. Download and extract `football-scouting-milestone-4.zip`.
2. In GitHub Desktop select **Repository → Show in Explorer**.
3. Open the extracted Milestone 4 folder and press **Ctrl+A**, then **Ctrl+C**.
4. Paste into the root of `Football-scouting-model`.
5. Select **Merge folders** or **Replace files in the destination** when prompted.
6. Confirm your raw CSV remains at:
   `data/raw/players_data-2025_2026.csv`
7. In GitHub Desktop, review the changed files.
8. Enter this summary:
   `Add Milestone 4 master dataset builder`
9. Click **Commit to main**.
10. Click **Push origin**.

Optional local check:

```bash
python scripts/build_master_dataset.py
```

Expected result:

```text
Master dataset built successfully.
```
