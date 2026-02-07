# ======================================================================================================================================================================
# MACHINE LEARNING FOR YU-GI-OH! REPLAYS
#
# Loads pre-built features and target CSVs (from DataProcessing_for_YGO.py) and
# trains/evaluates classification models.
# ======================================================================================================================================================================

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (works headless)
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def train_and_score_models(X: pd.DataFrame, y: pd.Series, *, test_size: float = 0.2, random_state: int = 1) -> dict[str, float]:
    if len(X) == 0:
        raise ValueError("No samples available after feature building (X is empty).")
    if len(X) < 2:
        raise ValueError(f"Not enough samples to train/test split (n_samples={len(X)}).")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    scores: dict[str, float] = {}

    # KNN requires n_neighbors <= n_train
    n_neighbors = min(11, len(X_train))
    n_neighbors = max(1, n_neighbors)
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(X_train, y_train)
    scores["knn"] = float(knn.score(X_test, y_test))

    # Some models require at least 2 classes in the training set
    if getattr(y_train, "nunique", None) is not None and int(y_train.nunique()) < 2:
        return scores

    logistic_regression = LogisticRegression(max_iter=200)
    logistic_regression.fit(X_train, y_train)
    scores["logistic_regression"] = float(logistic_regression.score(X_test, y_test))

    decision_tree = DecisionTreeClassifier(criterion="entropy", max_depth=10, random_state=random_state)
    decision_tree.fit(X_train, y_train)
    scores["decision_tree"] = float(decision_tree.score(X_test, y_test))

    random_forest = RandomForestClassifier(criterion="entropy", n_estimators=200, max_depth=10, random_state=random_state)
    random_forest.fit(X_train, y_train)
    scores["random_forest"] = float(random_forest.score(X_test, y_test))

    svc = SVC(kernel="rbf", random_state=random_state)
    svc.fit(X_train, y_train)
    scores["svc"] = float(svc.score(X_test, y_test))

    gradient_boosting = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=random_state)
    gradient_boosting.fit(X_train, y_train)
    scores["gradient_boosting"] = float(gradient_boosting.score(X_test, y_test))

    adaboost = AdaBoostClassifier(n_estimators=50, random_state=random_state)
    adaboost.fit(X_train, y_train)
    scores["adaboost"] = float(adaboost.score(X_test, y_test))

    naive_bayes = GaussianNB()
    naive_bayes.fit(X_train, y_train)
    scores["naive_bayes"] = float(naive_bayes.score(X_test, y_test))

    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=random_state)
    mlp.fit(X_train, y_train)
    scores["mlp"] = float(mlp.score(X_test, y_test))

    return scores


def plot_model_scores(scores: dict[str, float], out_path: Path | None = None) -> None:
    """Plot model accuracy scores as a horizontal bar chart."""
    models = list(scores.keys())
    accuracies = [scores[m] for m in models]
    colors = plt.cm.viridis([a / max(accuracies) if accuracies else 0 for a in accuracies])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(models, accuracies, color=colors)
    ax.set_xlabel("Accuracy")
    ax.set_xlim(0, 1)
    ax.axvline(x=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_title("Model comparison (test accuracy)")
    fig.tight_layout()

    if out_path:
        out_path = Path(out_path).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        print(f"✅ Plot saved to: {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate ML models on pre-built features and target CSVs.")
    parser.add_argument(
        "--features",
        type=Path,
        default=_PROJECT_ROOT / "data/matches_data_features_Fryderyk Chopin.csv",
        help="Input features CSV",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=_PROJECT_ROOT / "data/target_variable_Fryderyk Chopin.csv",
        help="Input target variable CSV (game1_winner)",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=1)
    parser.add_argument(
        "--plot-out",
        type=Path,
        default=_PROJECT_ROOT / "data/model_comparison.png",
        help="Save bar chart of model scores to this path",
    )
    parser.add_argument("--no-plot", action="store_true", help="Skip visualization (for headless/CI)")
    args = parser.parse_args(argv)

    X = pd.read_csv(Path(args.features).expanduser().resolve())
    y = pd.read_csv(Path(args.target).expanduser().resolve()).squeeze("columns")
    if y.name is None:
        y.name = "game1_winner"

    print(f"Loaded X: {X.shape}, y: {y.shape}")
    scores = train_and_score_models(X, y, test_size=args.test_size, random_state=args.random_state)
    for k, v in scores.items():
        print(f"{k}: {v}")

    if not args.no_plot:
        plot_model_scores(scores, out_path=args.plot_out)

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