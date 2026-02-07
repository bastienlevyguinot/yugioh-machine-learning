# Yu-Gi-Oh! Machine Learning

Machine learning project to predict duel outcomes from DuelingBook replay data (Fryderyk Chopin dataset).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Pipeline

The pipeline has two steps: **data processing** (matches CSV → features + target) and **machine learning** (train and evaluate models).

### 1. Data processing

Reads `data/matches_data_Fryderyk Chopin.csv`, builds features and target variable, saves to:

- `data/matches_data_features_Fryderyk Chopin.csv`
- `data/target_variable_Fryderyk Chopin.csv`

```bash
python scripts/DataProcessing_for_YGO.py
```

Options: `--csv`, `--replays-dir`, `--features-out`, `--target-out`, `--no-deck-filter`, `--provider`

### 2. Machine learning

Reads the features and target CSVs, trains classifiers, prints scores, saves a comparison plot.

```bash
python scripts/ML_for_YGO.py
```

Outputs: `data/model_comparison.png` (bar chart of model accuracies)

Options: `--features`, `--target`, `--plot-out`, `--no-plot`, `--test-size`, `--random-state`

## Data

| File | Description |
|------|-------------|
| `data/db_replays/` | Replay JSON files from DuelingBook |
| `data/matches_data_Fryderyk Chopin.csv` | Matches table (built from replays) |
| `data/matches_data_features_Fryderyk Chopin.csv` | Feature matrix for ML |
| `data/target_variable_Fryderyk Chopin.csv` | Target: `game1_winner` (True/False) |

## Optional: build matches CSV from replays

If you have replay JSONs in `data/db_replays/` but no matches CSV yet:

```bash
python scripts/get_csv_from_json.py --replays-dir data/db_replays --out "data/matches_data_Fryderyk Chopin.csv" --provider "Fryderyk Chopin"
```

## Optional: scrape new replays

Requires Chrome and ChromeDriver. Fetches replay JSONs from DuelingBook (handles reCAPTCHA via Selenium).

Single replay:

```bash
python scripts/get_db_match_selenium_clean.py --replay "1313181-76237082" --out-dir data/db_replays
```

From a links file (xlsx/csv/txt/json):

```bash
python scripts/get_db_match_selenium_clean.py --links-file path/to/links.csv --out-dir data/db_replays
```

## Project structure

```
scripts/
  DataProcessing_for_YGO.py   # Matches CSV → features + target
  ML_for_YGO.py              # Train/evaluate classifiers, plot results
  get_csv_from_json.py       # Replay JSONs → matches CSV
  get_db_match_selenium_clean.py  # Scrape replay JSONs from DuelingBook
  clean_replay_links.py      # Extract replay URLs from browser console JSON
data/
  db_replays/                # Replay JSON files
  matches_data_Fryderyk Chopin.csv
  matches_data_features_Fryderyk Chopin.csv
  target_variable_Fryderyk Chopin.csv
  model_comparison.png       # Visualization of model scores
```

## Models

KNN, logistic regression, decision tree, random forest, SVC, gradient boosting, AdaBoost, naive Bayes, MLP.
