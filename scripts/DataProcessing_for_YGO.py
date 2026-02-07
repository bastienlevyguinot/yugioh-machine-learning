"""
Data processing for Yu-Gi-Oh! replay matches.

Reads a matches CSV, builds features (card columns, etc.), and writes a features CSV.
Used to prepare data before ML training.

Usage:
  python scripts/DataProcessing_for_YGO.py
  python scripts/DataProcessing_for_YGO.py --csv data/matches.csv --features-out data/features.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Filter by deck choice - assuming player1 is our data provider
LIST_PLAYS = ["Normal Summon", "Declare", "Activate ST", "To GY", "SS ATK", "Banish", "SS DEF"]
TARGETED_CARDS = [
    "R.B. Ga10 Driller",
    "Jet Synchron",
    "R.B. Last Stand",
    "R.B. Ga10 Cutter",
    "Scrap Recycler",
    "R.B. Funk Dock",
    "R.B. Stage Landing",
    "R.B. Lambda Cannon",
    "R.B. Lambda Blade",
    "R.B. Ga10 Pile Bunker",
]
DATA_PROVIDER_USERNAME = "Fryderyk Chopin"


def load_dataset(csv_path: Path) -> pd.DataFrame:
    path = Path(csv_path).expanduser().resolve()
    return pd.read_csv(path)


def using_wrong_deck(
    dataset: pd.DataFrame,
    index_file: int,
    replays_dir: Path,
    *,
    data_provider_username: str,
) -> bool:
    """
    Returns True if wrong deck (no targeted plays/cards found), False if correct deck.
    """
    file_name_json = dataset.loc[index_file, "file"]
    replay_path = (replays_dir / str(file_name_json)).expanduser().resolve()
    if not replay_path.exists():
        print(f"⚠️  Fichier introuvable: {replay_path} — ligne ignorée (vérifiez --replays-dir)")
        return True
    try:
        with open(replay_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️  Erreur lecture {replay_path.name}: {e} — ligne ignorée")
        return True
    for play in data.get("plays", []):
        if (
            (play["play"] in LIST_PLAYS)
            and (play.get("card", {}).get("name") in TARGETED_CARDS)
            and (play.get("username") == data_provider_username)
        ):
            return False
    return True


def build_features(
    dataset: pd.DataFrame,
    replays_dir: Path,
    *,
    drop_indices: list[int] | None = None,
    filter_wrong_deck: bool = True,
    data_provider_username: str = DATA_PROVIDER_USERNAME,
) -> tuple[pd.DataFrame, pd.Series]:
    dataset = dataset.copy()
    dataset = dataset.dropna(subset=["file"]).reset_index(drop=True)

    dataset["game1_winner"] = dataset["game1_winner"].astype("boolean")
    dataset = dataset.dropna(subset=["game1_winner"]).reset_index(drop=True)

    if drop_indices:
        existing = [i for i in drop_indices if 0 <= i < len(dataset)]
        if existing:
            dataset = dataset.drop(index=existing).reset_index(drop=True)

    if filter_wrong_deck:
        to_drop = [
            idx
            for idx in dataset.index
            if using_wrong_deck(dataset, idx, replays_dir, data_provider_username=data_provider_username)
        ]
        dataset = dataset.drop(index=to_drop).reset_index(drop=True)

    dataset["starting_hand_player1"] = dataset["starting_hand_player1"].apply(lambda x: str(x).split("%%%%")[0:5])
    dataset["starting_hand_player2"] = dataset["starting_hand_player2"].apply(lambda x: str(x).split("%%%%")[0:5])

    unique_cards_p1: list[str] = []
    for hand in dataset["starting_hand_player1"]:
        for card in hand:
            if card and card not in unique_cards_p1:
                unique_cards_p1.append(card)
    for card in unique_cards_p1:
        dataset[f"{card} (player1)"] = 0

    for i in range(len(dataset["starting_hand_player1"])):
        for card in dataset.loc[i, "starting_hand_player1"]:
            dataset.loc[i, f"{card} (player1)"] += 1

    X = dataset.drop(
        columns=["game1_winner", "file", "starting_hand_player1", "starting_hand_player2", "player1", "player2"]
    )
    y = dataset["game1_winner"]
    return X, y


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process matches CSV and output features CSV.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_PROJECT_ROOT / "data/matches_data_Fryderyk Chopin.csv",
        help="Input matches CSV",
    )
    parser.add_argument(
        "--replays-dir",
        type=Path,
        default=_PROJECT_ROOT / "data/db_replays",
        help="Directory containing replay JSON files",
    )
    parser.add_argument(
        "--features-out",
        type=Path,
        default=_PROJECT_ROOT / "data/matches_data_features_Fryderyk Chopin.csv",
        help="Output features CSV",
    )
    parser.add_argument(
        "--target-out",
        type=Path,
        default=_PROJECT_ROOT / "data/target_variable_Fryderyk Chopin.csv",
        help="Output target variable CSV",
    )
    parser.add_argument("--drop-index", type=int, action="append", default=[], help="Row indices to drop (optional)")
    parser.add_argument(
        "--no-deck-filter",
        action="store_true",
        help="Disable the deck-specific 'wrong deck' filter.",
    )
    parser.add_argument("--provider", type=str, default=DATA_PROVIDER_USERNAME, help="Username for deck filtering")
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

    y.to_csv(args.target_out, index=False, header=["game1_winner"])
    print(f"✅ Target variable CSV saved to: {args.target_out} (shape={y.shape})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
