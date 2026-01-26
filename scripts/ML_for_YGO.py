# ======================================================================================================================================================================
# THIS CODE AIMS TO IMPORT OUR DATA (from .csv), PROCESS IT, EXPLORE DIFFERENT MACHINE LEARNING MODELS AND EVALUATE THEM
# ======================================================================================================================================================================

from re import L
import pandas as pd

# Import dataset
# working directory is Desktop, needs to be seted-up as our file ML_for_YGO
dataset = pd.read_csv("matches_data_mitsu_RB.csv") # voir get_csv_from_json.py pour le lien
# colonnes : ['file', 'player1', 'player2', 'rps_winner', 'game1_winner', 'starting_hand_player1', 'starting_hand_player2']
# Dtype/colonne : [object, object, object, bool, bool, object, object]

# DATA PROCESSING ==========================================================================================================================================================

from sklearn.model_selection import train_test_split
import json

# filter by deck choice - assuming the player1 is our data provider
list_plays = ['Normal Summon', 'Declare', 'Activate ST', 'To GY', 'SS ATK', 'Banish', 'SS DEF']
targeted_cards = ['R.B. Ga10 Driller', 'Jet Synchron', 'R.B. Last Stand', 'R.B. Ga10 Cutter', 'Scrap Recycler', 'R.B. Funk Dock', 'R.B. Stage Landing', 'R.B. Lambda Cannon', 'R.B. Lambda Blade', 'R.B. Ga10 Pile Bunker']
DATA_PROVIDER_USERNAME = "Fryderyk Chopin"

def using_wrong_deck(index_file):
    # True  -> wrong deck (no targeted plays/cards found)
    # False -> correct deck (targeted play/card found)
    file_name_json = dataset.loc[index_file, "file"]
    with open(f"/Users/BastienLevy-Guinot/Desktop/db_replays/{file_name_json}", "r") as f:
        data = json.load(f)

        # print("================="+str(index_file)+"=================="+str(dataset.loc[index_file, 'file'])+"=============")
        for play in data['plays']:

            # if True :
            #     if play['play'] in list_plays:
            #         print("Play is : " + str(play['play']))
            #         if play.get('username') == DATA_PROVIDER_USERNAME:
            #             print("Username is : " + str(play.get('username')))
            #             if play['card'].get('name') in targeted_cards:
            #                 print("Card is : " + str(play['card'].get('name')))
            #             else:
            #                 print("Card is not in targeted cards, card is " + str(play['card'].get('name')))
            #         else:
            #             print("Username isnt correct")
                
            if (play['play'] in list_plays) and (play['card'].get('name') in targeted_cards) and (play.get('username') == DATA_PROVIDER_USERNAME):
                # print("RETURN FALSE, CORRECT DECK")
                return False
        # print("RETURN TRUE, WRONG DECK")
        return True

# Drop all rows that are detected as "wrong deck"

to_drop = [idx for idx in dataset.index if using_wrong_deck(idx)]
dataset = dataset.drop(index=to_drop).reset_index(drop=True)
dataset = dataset.drop(index=113).reset_index(drop=True) # specific column misinterpreted
dataset = dataset.drop(index=44).reset_index(drop=True) # game not played, game_winner = NaN
dataset = dataset.drop(index=31).reset_index(drop=True) # game not played, game_winner = NaN
dataset = dataset.drop(index=2).reset_index(drop=True) # game not played, game_winner = NaN
dataset["game1_winner"] = dataset["game1_winner"].astype("boolean")
dataset['game1_winner'] = dataset['game1_winner'].fillna(True)

# starting_hands from string to list
dataset['starting_hand_player1'] = dataset['starting_hand_player1'].apply(lambda x: x.split("%%%%")[0:5])
dataset['starting_hand_player2'] = dataset['starting_hand_player2'].apply(lambda x: x.split("%%%%")[0:5])

# Which plays are associated to card actions ?
# list_plays = ['Normal Summon', 'Declare', 'Activate ST', 'To GY', 'SS ATK', 'Banish', 'SS DEF'] 
# list_cards_player1 = []

# creating columns for each card name used in the matches - player 1
for starting_hand_player1 in dataset['starting_hand_player1']:
    for i in range (len(starting_hand_player1)):
        # list_cards_player1.append(starting_hand_player1[i])
        dataset[str(starting_hand_player1[i])+" (player1)"] = [0 for j in range(len(dataset['starting_hand_player1']))]


# list_cards_player1_unique = []
# [list_cards_player1_unique.append(card) for card in list_cards_player1 if card not in list_cards_player1_unique]
# Which are played by the player1 - we assume the player1 is our data provider

# creating columns for each card name used in the matches - player 2
"""for starting_hand_player2 in dataset['starting_hand_player2']:
    for i in range (len(starting_hand_player2)):
        dataset[str(starting_hand_player2[i]) + " (player2)"] = [0 for j in range(len(dataset['starting_hand_player2']))]"""

# Fill cards' columns with the data in 'starting_hand_player1'
for i in  range (len(dataset['starting_hand_player1'])):
    for card in dataset.loc[i, 'starting_hand_player1']:
        dataset.loc[i, str(card)+" (player1)"] += 1

# Fill cards' columns with the data in 'starting_hand_player2'
"""for i in  range (len(dataset['starting_hand_player2'])):
   for card in dataset.loc[i, 'starting_hand_player2']:
        dataset.loc[i, str(card)+" (player2)"] += 1"""

# output_file = "/Users/BastienLevy-Guinot/Desktop/matches_data_mitsu_RB_1.0.csv"
# dataset.to_csv(output_file, index=False)


X = dataset.drop(columns=["game1_winner", "file", "starting_hand_player1", "starting_hand_player2", 'player1', 'player2']) # features , drop 'file' ?
y = dataset["game1_winner"] # target variable

output_file = "/Users/BastienLevy-Guinot/Desktop/matches_data_mitsu_RB_2.0.csv"
X.to_csv(output_file, index=False)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1) # how should we choose the test_size ?

# EXPLORING MODELS =======================================================================================================================================================================

from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

knn = KNeighborsClassifier(n_neighbors=11) # How should we choose the n_neighbors
knn.fit(X_train, y_train)
print("Score of knn is : " + str(knn.score(X_test, y_test)))

logistic_regression = LogisticRegression(max_iter=100) # How should we fix the max_iter
logistic_regression.fit(X_train, y_train)
print("Score of logistic_regression is : " + str(logistic_regression.score(X_test, y_test)))

decision_tree = DecisionTreeClassifier(criterion="entropy", max_depth=10, random_state=0)
decision_tree.fit(X_train, y_train)
print("Score of decision tree is : " + str(decision_tree.score(X_test, y_test)))

random_forest = RandomForestClassifier(criterion="entropy", n_estimators=100, max_depth=10)
random_forest.fit(X_train, y_train)
print("Score of random forest is : " + str(random_forest.score(X_test, y_test)))

print(list(X_train.columns()))
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