"""
Run the end-to-end pipeline from this repository.

Pipeline (offline):
  1) Build a matches CSV from replay JSONs (data/db_replays -> data/matches_data_mitsu_RB.csv)
  2) Build features + train/evaluate baseline models (-> data/matches_data_mitsu_RB_2.0.csv)

Pipelines:
  - offline: use an existing db_replays folder (NO scraping)
  - from-excel: start ONLY from an Excel/CSV/TXT links file, scrape JSONs into db_replays, then run offline steps

Usage:
  python scripts/run_pipeline.py offline
  python scripts/run_pipeline.py offline --replays-dir data/db_replays
  python scripts/run_pipeline.py from-excel --links-file my_links.xlsx
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from get_csv_from_json import build_matches_dataframe
from ML_for_YGO import build_features, load_dataset, train_and_score_models


def _count_json_files(dir_path: Path) -> int:
    try:
        return sum(1 for p in dir_path.glob("*.json") if p.is_file())
    except Exception:
        return 0


def _scrape_replays(
    *,
    links_file: Path,
    out_dir: Path,
    profile_dir: str | None,
    keep_user_prefix: bool,
) -> None:
    """
    Scrape replay JSONs (using Selenium) into out_dir from a links file.
    """
    # Local import so users can run the offline pipeline without Selenium deps installed.
    from get_db_match_selenium_clean import read_links_from_file, scrape_one

    links: Iterable[str] = read_links_from_file(links_file)

    failures = 0
    for link in links:
        failures += (
            1
            if scrape_one(
                link,
                out_dir=out_dir,
                profile_dir=profile_dir,
                strip_user_prefix=not keep_user_prefix,
            )
            != 0
            else 0
        )

    if failures:
        raise RuntimeError(f"Scraping finished with {failures} failure(s). See logs above.")

def _run_offline(
    *,
    replays_dir: Path,
    provider: str,
    matches_csv: Path,
    features_out: Path,
    skip_build_csv: bool,
) -> int:
    replays_dir_resolved = replays_dir.expanduser().resolve()
    print(f"Replays dir: {replays_dir_resolved} (json files: {_count_json_files(replays_dir_resolved)})")

    if not skip_build_csv:
        df = build_matches_dataframe(replays_dir, data_provider_username=provider)
        matches_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(matches_csv, index=False)
        print(f"✅ Matches CSV saved to: {matches_csv} (rows={len(df)})")

    dataset = load_dataset(matches_csv)
    X, y = build_features(dataset, replays_dir)
    features_out.parent.mkdir(parents=True, exist_ok=True)
    X.to_csv(features_out, index=False)
    print(f"✅ Features CSV saved to: {features_out} (shape={X.shape})")

    scores = train_and_score_models(X, y)
    print("Scores:")
    for k, v in scores.items():
        print(f"  - {k}: {v}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="End-to-end pipeline runner (offline vs from-excel).")
    sub = parser.add_subparsers(dest="mode", required=True)

    # offline: only uses an existing db_replays folder (no scraping)
    p_off = sub.add_parser("offline", help="Use an existing db_replays folder (no scraping).")
    p_off.add_argument("--replays-dir", type=Path, default=Path("data/db_replays"))
    p_off.add_argument("--provider", type=str, default="Fryderyk Chopin", help="Username to force into player1 (optional).")
    p_off.add_argument("--matches-csv", type=Path, default=Path("data/matches_data_mitsu_RB.csv"))
    p_off.add_argument("--features-out", type=Path, default=Path("data/matches_data_mitsu_RB_2.0.csv"))
    p_off.add_argument("--skip-build-csv", action="store_true")

    # from-excel: start only from a links file, scrape JSONs, then run offline
    p_fx = sub.add_parser("from-excel", help="Start only from a links file, scrape JSONs, then run offline steps.")
    p_fx.add_argument("--links-file", type=Path, required=True, help="xlsx/csv/txt containing replay ids/urls")
    p_fx.add_argument("--replays-dir", type=Path, default=Path("data/db_replays"), help="Where to store scraped JSON replay files")
    p_fx.add_argument("--profile-dir", type=str, default=None, help="Optional Chrome user-data-dir (for replays requiring login)")
    p_fx.add_argument("--keep-user-prefix", action="store_true", help="Do not strip userId from ids like 745183-77512517")
    p_fx.add_argument("--provider", type=str, default="Fryderyk Chopin", help="Username to force into player1 (optional).")
    p_fx.add_argument("--matches-csv", type=Path, default=Path("data/matches_data_mitsu_RB.csv"))
    p_fx.add_argument("--features-out", type=Path, default=Path("data/matches_data_mitsu_RB_2.0.csv"))

    args = parser.parse_args(argv)

    if args.mode == "offline":
        return _run_offline(
            replays_dir=args.replays_dir,
            provider=args.provider,
            matches_csv=args.matches_csv,
            features_out=args.features_out,
            skip_build_csv=args.skip_build_csv,
        )

    if args.mode == "from-excel":
        _scrape_replays(
            links_file=args.links_file,
            out_dir=args.replays_dir,
            profile_dir=args.profile_dir,
            keep_user_prefix=args.keep_user_prefix,
        )
        return _run_offline(
            replays_dir=args.replays_dir,
            provider=args.provider,
            matches_csv=args.matches_csv,
            features_out=args.features_out,
            skip_build_csv=False,
        )

    raise RuntimeError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())

