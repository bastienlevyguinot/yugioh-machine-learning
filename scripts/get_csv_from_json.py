# Dans ce fichier, on va faire du machine learning sur les données de DuelingBook.
# On va utiliser le fichier json contenant les données de chaque match.
# Location of the json files : /Users/BastienLevy-Guinot/Desktop/db_replays/

import json
import pandas as pd
import os
import numpy as np

def get_player_name(data_json):
    for play in data_json['plays']:
            if play['play']=='RPS':
                return play['player1'], play['player2']
    return None, None  # Retourner None si aucun play RPS n'est trouvé

def get_RPS_winner(data_json):
    for play in data_json['plays']:
            if play['play']=='RPS':
                # Retourne True si player1 a gagné, False si player2 a gagné
                return play['player1'] == play['winner']
    return None  # Aucun play RPS trouvé

def get_game1_winner(data_json, player1_name, player2_name):
    for play in data_json['plays']:
            if play['play']=='Admit defeat':
                # Si player2 a admis la défaite, alors player1 a gagné (retourne True)
                # Si player1 a admis la défaite, alors player2 a gagné (retourne False)
                if 'username' in play:
                    return play['username'] != player1_name  # True si player1 a gagné
    return None  # Aucun "Admit defeat" trouvé


def get_start_hands(data_json):
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

def get_list_of_plays(data_json):
    l = []
    for play in data_json['plays']:
        l.append(play['play'])
    l_unique = []
    [l_unique.append(play) for play in l if play not in l_unique]
    return l_unique

# Liste pour stocker toutes les données des matches
matches_data = []

# json_files is a list of all the json files in the directory
json_files = [f for f in os.listdir("/Users/BastienLevy-Guinot/Desktop/db_replays/") if f.endswith(".json")]

# Load the json files
for file in json_files:
    total_plays = []
    with open(f"/Users/BastienLevy-Guinot/Desktop/db_replays/{file}", "r") as f:
        data = json.load(f)

        player1_name, player2_name = get_player_name(data)
        
        # Vérifier si les noms ont été trouvés
        if player1_name is None or player2_name is None:
            print(f"⚠️  Aucun play RPS trouvé dans {file} - ignoré")
            continue  # Passer au fichier suivant
        
        # Récupérer les données
        rps_winner = get_RPS_winner(data)  # True si player1 gagne, False si player2 gagne
        game1_winner = get_game1_winner(data, player1_name, player2_name)  # True si player1 gagne, False si player2 gagne
        hand_player1, hand_player2 = get_start_hands(data)

        total_plays += get_list_of_plays(data)
        
        # Stocker les données dans un dictionnaire
        match_data = {
            'file': file,
            'player1': player1_name,
            'player2': player2_name,
            'rps_winner': rps_winner,  # True = player1, False = player2, None = indéterminé
            'game1_winner': game1_winner,  # True = player1, False = player2, None = indéterminé
            'starting_hand_player1': hand_player1,
            'starting_hand_player2': hand_player2
        }
        total_plays_unique = []
        [total_plays_unique.append(play) for play in total_plays if play not in total_plays_unique]
        matches_data.append(match_data)

print(total_plays)
# Créer le DataFrame pandas
df = pd.DataFrame(matches_data)

print("=" * 60)
print(f"DataFrame créé avec {len(df)} matches")
print("=" * 60)
print()
print("Aperçu du DataFrame:")
print(df.head())
print()
print("Colonnes disponibles:")
print(df.columns.tolist())

# In case my data provider being 'Fryderyk Chopin'
for i in range (len(df['file'])):
    if df.loc[i,'player2'] == 'Fryderyk Chopin':
        df.loc[i, 'player1'], df.loc[i, 'player2'] = df.loc[i, 'player2'], df.loc[i, 'player1']
        df.loc[i, 'starting_hand_player1'], df.loc[i, 'starting_hand_player2'] = df.loc[i, 'starting_hand_player2'], df.loc[i, 'starting_hand_player1']


# Sauvegarder le DataFrame en CSV pour inspection
output_file = "/Users/BastienLevy-Guinot/Desktop/matches_data_mitsu_RB.csv"
df.to_csv(output_file, index=False)
print(f"✅ DataFrame sauvegardé dans: {output_file}")

