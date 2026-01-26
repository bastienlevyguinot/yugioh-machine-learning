# ======================================================================================================================================================================
# THIS CODE AIMS TO IMPORT OUR DATA (from .csv), PROCESS IT, EXPLORE DIFFERENT MACHINE LEARNING MODELS AND EVALUATE THEM
# ======================================================================================================================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

def load_dataset(csv_path: Path) -> pd.DataFrame:
    csv_path = csv_path.expanduser().resolve()
    return pd.read_csv(csv_path)

# DATA PROCESSING ==========================================================================================================================================================

from sklearn.model_selection import train_test_split

# filter by deck choice - assuming the player1 is our data provider
list_plays = ['Normal Summon', 'Declare', 'Activate ST', 'To GY', 'SS ATK', 'Banish', 'SS DEF']
targeted_cards = ['R.B. Ga10 Driller', 'Jet Synchron', 'R.B. Last Stand', 'R.B. Ga10 Cutter', 'Scrap Recycler', 'R.B. Funk Dock', 'R.B. Stage Landing', 'R.B. Lambda Cannon', 'R.B. Lambda Blade', 'R.B. Ga10 Pile Bunker']
DATA_PROVIDER_USERNAME = "Fryderyk Chopin"

def using_wrong_deck(
    dataset: pd.DataFrame,
    index_file: int,
    replays_dir: Path,
    *,
    data_provider_username: str,
) -> bool:
    # True  -> wrong deck (no targeted plays/cards found)
    # False -> correct deck (targeted play/card found)
    file_name_json = dataset.loc[index_file, "file"]
    replay_path = (replays_dir / str(file_name_json)).expanduser().resolve()
    with open(replay_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for play in data['plays']:
                
            if (
                (play['play'] in list_plays)
                and (play['card'].get('name') in targeted_cards)
                and (play.get('username') == data_provider_username)
            ):
                # print("RETURN FALSE, CORRECT DECK")
                return False
        # print("RETURN TRUE, WRONG DECK")
        return True

def build_features(
    dataset: pd.DataFrame,
    replays_dir: Path,
    *,
    drop_indices: list[int] | None = None,
    filter_wrong_deck: bool = True,
    data_provider_username: str = DATA_PROVIDER_USERNAME,
) -> tuple[pd.DataFrame, pd.Series]:
    # Drop rows with missing target/hand information (more robust than hardcoded indices)
    dataset = dataset.copy()
    dataset = dataset.dropna(subset=["file"]).reset_index(drop=True)

    # Some rows have game not played -> NaN winner
    dataset["game1_winner"] = dataset["game1_winner"].astype("boolean")
    dataset = dataset.dropna(subset=["game1_winner"]).reset_index(drop=True)

    # Optional legacy drops (kept for backwards compatibility with earlier experiments)
    if drop_indices:
        existing = [i for i in drop_indices if 0 <= i < len(dataset)]
        if existing:
            dataset = dataset.drop(index=existing).reset_index(drop=True)

    # Drop all rows detected as "wrong deck" (optional; deck-specific heuristic)
    if filter_wrong_deck:
        to_drop = [
            idx
            for idx in dataset.index
            if using_wrong_deck(dataset, idx, replays_dir, data_provider_username=data_provider_username)
        ]
        dataset = dataset.drop(index=to_drop).reset_index(drop=True)

    # starting_hands from string to list
    dataset["starting_hand_player1"] = dataset["starting_hand_player1"].apply(lambda x: str(x).split("%%%%")[0:5])
    dataset["starting_hand_player2"] = dataset["starting_hand_player2"].apply(lambda x: str(x).split("%%%%")[0:5])

    # Create columns for each card name used in the matches - player 1
    unique_cards_p1: list[str] = []
    for hand in dataset["starting_hand_player1"]:
        for card in hand:
            if card and card not in unique_cards_p1:
                unique_cards_p1.append(card)
    for card in unique_cards_p1:
        dataset[f"{card} (player1)"] = 0

    # Fill cards' columns with the data in 'starting_hand_player1'
    for i in range(len(dataset["starting_hand_player1"])):
        for card in dataset.loc[i, "starting_hand_player1"]:
            dataset.loc[i, f"{card} (player1)"] += 1

    X = dataset.drop(columns=["game1_winner", "file", "starting_hand_player1", "starting_hand_player2", "player1", "player2"])
    y = dataset["game1_winner"]
    return X, y

# EXPLORING MODELS =======================================================================================================================================================================

from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

def train_and_score_models(X: pd.DataFrame, y: pd.Series, *, test_size: float = 0.2, random_state: int = 1) -> dict[str, float]:
    if len(X) == 0:
        raise ValueError("No samples available after feature building (X is empty).")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    scores: dict[str, float] = {}

    knn = KNeighborsClassifier(n_neighbors=11)
    knn.fit(X_train, y_train)
    scores["knn"] = float(knn.score(X_test, y_test))

    logistic_regression = LogisticRegression(max_iter=200)
    logistic_regression.fit(X_train, y_train)
    scores["logistic_regression"] = float(logistic_regression.score(X_test, y_test))

    decision_tree = DecisionTreeClassifier(criterion="entropy", max_depth=10, random_state=0)
    decision_tree.fit(X_train, y_train)
    scores["decision_tree"] = float(decision_tree.score(X_test, y_test))

    random_forest = RandomForestClassifier(criterion="entropy", n_estimators=200, max_depth=10, random_state=0)
    random_forest.fit(X_train, y_train)
    scores["random_forest"] = float(random_forest.score(X_test, y_test))

    return scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("data/matches_data_Fryderyk Chopin.csv"))
    parser.add_argument("--replays-dir", type=Path, default=Path("data/db_replays"))
    parser.add_argument("--features-out", type=Path, default=Path("data/matches_data_features_Fryderyk Chopin.csv"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=1)
    parser.add_argument("--drop-index", type=int, action="append", default=[])
    parser.add_argument(
        "--no-deck-filter",
        action="store_true",
        help="Disable the deck-specific 'wrong deck' filter (recommended for generic datasets).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=DATA_PROVIDER_USERNAME,
        help="Username to use for deck filtering (only relevant if deck filter is enabled).",
    )
    args = parser.parse_args(argv)

    dataset = load_dataset(args.csv)
    X, y = build_features(
        dataset,
        args.replays_dir,
        drop_indices=args.drop_index or None,
        filter_wrong_deck=not args.no_deck_filter,
        data_provider_username=args.provider,
    )

    args.features_out.parent.mkdir(parents=True, exist_ok=True)
    X.to_csv(args.features_out, index=False)
    print(f"✅ Features CSV saved to: {args.features_out} (shape={X.shape})")

    scores = train_and_score_models(X, y, test_size=args.test_size, random_state=args.random_state)
    for k, v in scores.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TREE VISUALISATION =======================================================================================================================================================================

"""from matplotlib import pyplot as plt
from sklearn import tree

decision_tree_vis = DecisionTreeClassifier(criterion="entropy", max_depth=3)
decision_tree_vis.fit(X_train, y_train)

fig = plt.figure(figsize=(25,20))
_ = tree.plot_tree(decision_tree_vis,
                   feature_names=X_train.columns,
                   class_names=y_train,
                   filled=True)"""