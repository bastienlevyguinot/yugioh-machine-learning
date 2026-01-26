# yugioh-machine-learning

## Run from this GitHub repo

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the offline pipeline (no scraping)

This uses the committed replay JSON files in `data/db_replays/`.

```bash
python scripts/run_pipeline.py
```

Outputs:
- `data/matches_data_mitsu_RB.csv` (built from `data/db_replays/`)
- `data/matches_data_mitsu_RB_2.0.csv` (features for ML)

### Run individual steps

Build the matches CSV:

```bash
python scripts/get_csv_from_json.py --replays-dir data/db_replays --out data/matches_data_mitsu_RB.csv --provider "Fryderyk Chopin"
```

Train/evaluate on an existing CSV:

```bash
python scripts/ML_for_YGO.py --csv data/matches_data_mitsu_RB.csv --replays-dir data/db_replays --features-out data/matches_data_mitsu_RB_2.0.csv
```

## What files are used vs legacy (high level)

Actively used for the runnable pipeline:
- `scripts/run_pipeline.py`
- `scripts/get_csv_from_json.py`
- `scripts/ML_for_YGO.py`
- `data/db_replays/` and `data/*.csv`

Optional (scraping new replays, requires Chrome + ChromeDriver):
- `scripts/get_duelingbook_match_selenium.py`
- `scripts/get_db_match_selenium_clean.py`
- `docs/INSTALL_CHROMEDRIVER.md`

Likely legacy / previously used experiments (not used by `scripts/run_pipeline.py`):
- `ML_for_YGO/*` (browser console scripts + older data snapshots)
- `assets/duelingbook_replay.html` (HTML snapshot for reference)
- `requirements/requirements_duelingbook.txt` (older requirements list; prefer `requirements.txt`)

## Scrape new replays (optional)

If you want to generate new JSON files like the ones in `data/db_replays/`, you can use:

```bash
python scripts/get_db_match_selenium_clean.py --replay "745183-77512517" --out-dir data/db_replays
```

Or from a list file (xlsx/csv/txt):

```bash
python scripts/get_db_match_selenium_clean.py --links-file path/to/links.xlsx --out-dir data/db_replays
```

If some replays require login, you can point Selenium at a local Chrome profile directory **on your machine** (do not commit it):

```bash
python scripts/get_db_match_selenium_clean.py --replay "745183-77512517" --profile-dir "/absolute/path/to/chrome_profile" --out-dir data/db_replays
```

