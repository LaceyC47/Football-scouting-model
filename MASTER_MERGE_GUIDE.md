# Install and Run the Master Merge Engine

## 1. Add the files to the repository

1. Extract this ZIP.
2. In GitHub Desktop select **Repository → Show in Explorer**.
3. Copy everything from the extracted folder into the root of `Football-scouting-model`.
4. Choose **Merge folders** or **Replace files in the destination** when prompted.

## 2. Commit

Use:

```text
Add master player merge engine
```

Then click **Commit to main** and **Push origin**.

## 3. Run

In the repository folder, click the File Explorer address bar, type `cmd`, and press Enter.

Run:

```cmd
python scripts\build_master_merge.py
```

## 4. Expected outputs

Main dataset:

```text
data\processed\master_player_dataset_v1.parquet
data\processed\master_player_dataset_v1.csv
```

Audit files:

```text
reports\merge
```

Upload the files in `reports\merge` after the run. The audit will tell us the true matching and coverage rates before we use the dataset for modelling.

## v1.3 fix

Fixed duplicate `_source_file` columns during sequential merges.

## v1.3 fix

Fixed SofaScore match-source identification and coverage reporting.
