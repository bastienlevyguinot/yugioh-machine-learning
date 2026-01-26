"""
Run the end-to-end pipeline from this repository.

Pipeline (offline):
  1) Build a matches CSV from replay JSONs (data/db_replays -> data/matches_data_mitsu_RB.csv)
  2) Build features + train/evaluate baseline models (-> data/matches_data_mitsu_RB_2.0.csv)

Usage:
  python scripts/run_pipeline.py
  python scripts/run_pipeline.py --skip-build-csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_csv_from_json import build_matches_dataframe
from ML_for_YGO import build_features, load_dataset, train_and_score_models


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replays-dir", type=Path, default=Path("data/db_replays"))
    parser.add_argument("--provider", type=str, default="Fryderyk Chopin")
    parser.add_argument("--matches-csv", type=Path, default=Path("data/matches_data_mitsu_RB.csv"))
    parser.add_argument("--features-out", type=Path, default=Path("data/matches_data_mitsu_RB_2.0.csv"))
    parser.add_argument("--skip-build-csv", action="store_true")
    args = parser.parse_args(argv)

    if not args.skip_build_csv:
        df = build_matches_dataframe(args.replays_dir, data_provider_username=args.provider)
        args.matches_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.matches_csv, index=False)
        print(f"✅ Matches CSV saved to: {args.matches_csv} (rows={len(df)})")

    dataset = load_dataset(args.matches_csv)
    X, y = build_features(dataset, args.replays_dir)
    args.features_out.parent.mkdir(parents=True, exist_ok=True)
    X.to_csv(args.features_out, index=False)
    print(f"✅ Features CSV saved to: {args.features_out} (shape={X.shape})")

    scores = train_and_score_models(X, y)
    print("Scores:")
    for k, v in scores.items():
        print(f"  - {k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

