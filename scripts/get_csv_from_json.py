"""
Build a CSV dataset from DuelingBook replay JSON files.

This script was originally written with absolute Desktop paths; it has been
refactored to run from this GitHub repository using relative paths.

Typical usage:
  python scripts/get_csv_from_json.py --replays-dir data/db_replays --out data/matches_data_mitsu_RB.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

def get_player_name(data_json: dict[str, Any]):
    for play in data_json['plays']:
            if play['play']=='RPS':
                return play['player1'], play['player2']
    return None, None  # Retourner None si aucun play RPS n'est trouvé

def get_RPS_winner(data_json: dict[str, Any]):
    for play in data_json['plays']:
            if play['play']=='RPS':
                # Retourne True si player1 a gagné, False si player2 a gagné
                return play['player1'] == play['winner']
    return None  # Aucun play RPS trouvé

def get_game1_winner(data_json: dict[str, Any], player1_name: str, player2_name: str):
    for play in data_json['plays']:
            if play['play']=='Admit defeat':
                # Si player2 a admis la défaite, alors player1 a gagné (retourne True)
                # Si player1 a admis la défaite, alors player2 a gagné (retourne False)
                if 'username' in play:
                    return play['username'] != player1_name  # True si player1 a gagné
    return None  # Aucun "Admit defeat" trouvé


def get_start_hands(data_json: dict[str, Any]):
    for play in data_json['plays']:
        if play['play']=='Pick first':
            cards_player1 = ""
            cards_player2 = ""
            cpt = 0
            for card in play['cards']:
                if cpt < 5 :
                    cards_player1 += card['name'] + "%%%%"
                else :
                    cards_player2 += card['name'] + "%%%%"
                cpt += 1
            # Les 5 premières cartes sont pour player1, les 5 suivantes pour player2
            return cards_player1, cards_player2
    return None, None

def get_list_of_plays(data_json: dict[str, Any]):
    l = []
    for play in data_json['plays']:
        l.append(play['play'])
    l_unique = []
    [l_unique.append(play) for play in l if play not in l_unique]
    return l_unique

def build_matches_dataframe(replays_dir: Path, data_provider_username: str | None = None) -> pd.DataFrame:
    replays_dir = replays_dir.expanduser().resolve()
    json_paths = sorted(p for p in replays_dir.glob("*.json") if p.is_file())

    matches_data: list[dict[str, Any]] = []
    total_plays: list[str] = []

    for path in json_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        player1_name, player2_name = get_player_name(data)
        if player1_name is None or player2_name is None:
            print(f"⚠️  Aucun play RPS trouvé dans {path.name} - ignoré")
            continue

        rps_winner = get_RPS_winner(data)
        game1_winner = get_game1_winner(data, player1_name, player2_name)
        hand_player1, hand_player2 = get_start_hands(data)

        total_plays += get_list_of_plays(data)

        match_data = {
            "file": path.name,
            "player1": player1_name,
            "player2": player2_name,
            "rps_winner": rps_winner,
            "game1_winner": game1_winner,
            "starting_hand_player1": hand_player1,
            "starting_hand_player2": hand_player2,
        }
        matches_data.append(match_data)

    df = pd.DataFrame(matches_data)

    if data_provider_username:
        # Ensure the data provider is always in player1
        for i in range(len(df["file"])):
            if df.loc[i, "player2"] == data_provider_username:
                df.loc[i, "player1"], df.loc[i, "player2"] = df.loc[i, "player2"], df.loc[i, "player1"]
                df.loc[i, "starting_hand_player1"], df.loc[i, "starting_hand_player2"] = (
                    df.loc[i, "starting_hand_player2"],
                    df.loc[i, "starting_hand_player1"],
                )

    total_plays_unique: list[str] = []
    [total_plays_unique.append(p) for p in total_plays if p not in total_plays_unique]
    print("Plays seen (unique):", total_plays_unique)

    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replays-dir", type=Path, default=Path("data/db_replays"))
    parser.add_argument("--out", type=Path, default=Path("data/matches_data_mitsu_RB.csv"))
    parser.add_argument("--provider", type=str, default="Fryderyk Chopin")
    args = parser.parse_args(argv)

    df = build_matches_dataframe(args.replays_dir, data_provider_username=args.provider)

    print("=" * 60)
    print(f"DataFrame créé avec {len(df)} matches")
    print("=" * 60)
    print("Aperçu du DataFrame:")
    print(df.head())
    print("Colonnes disponibles:")
    print(df.columns.tolist())

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"✅ DataFrame sauvegardé dans: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())