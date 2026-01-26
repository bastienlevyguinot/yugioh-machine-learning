"""
Script pour recuperer les donnees d'un match DuelingBook via l'API avec Selenium.
Utilise Selenium pour obtenir un token reCAPTCHA valide automatiquement.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse

import json
import sys

DEFAULT_OUT_DIR = Path("data/db_replays")
DEFAULT_TRY_IT_YOURSELF_LINKS = Path("data/empty_match_data.csv")
DEFAULT_TRY_IT_YOURSELF_REPLAYS_DIR = Path("data/my_own_db_replays")
DEFAULT_TRY_IT_YOURSELF_MATCHES_CSV = Path("data/my_matches.csv")
DEFAULT_TRY_IT_YOURSELF_FEATURES_CSV = Path("data/my_features.csv")

def _parse_replay_id_and_match(url_or_id: str) -> tuple[str, str | None]:
    """
    Extract replay id (and optional match index) from:
      - https://www.duelingbook.com/replay?id=...&match=2
      - https://www.duelingbook.com/view-replay?id=...&match=2
      - raw id: 1313181-76237082
      - raw id: 77512517
    """
    s = (url_or_id or "").strip()
    if not s:
        raise ValueError("Empty replay identifier")

    if s.startswith("http"):
        parsed = urlparse(s)
        qs = parse_qs(parsed.query)
        replay_id = (qs.get("id") or [None])[0]
        match = (qs.get("match") or [None])[0]
        if not replay_id:
            raise ValueError(f"Could not parse replay id from URL: {s}")
        return str(replay_id), (str(match) if match else None)

    return s, None


def _clean_link_value(value: object) -> str | None:
    """
    Normalize a raw cell/line into a replay id/url string.
    Returns None if the value should be ignored (empty/header/etc).
    """
    s = str(value).strip()
    if not s:
        return None

    # Common "empty" values coming from pandas
    if s.lower() in {"nan", "none", "null"}:
        return None

    # Remove surrounding quotes (common when users paste quoted CSV values)
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()
        if not s:
            return None

    # Ignore header-like rows accidentally pasted in the body
    if s.strip().lower() in {"url", "urls", "replay", "replay_id", "replay id", "id"}:
        return None

    return s

def get_replay_id(url_or_id: str) -> str:
    replay_id, match = _parse_replay_id_and_match(url_or_id)
    if match:
        return f"{replay_id}_match{match}"
    return replay_id

def get_recaptcha_token_and_cookies_with_selenium(replay_url: str, *, profile_dir: str | None = None):
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        raise RuntimeError(
            "Selenium is not installed."
        ) from e

    # Utilise Selenium pour obtenir un token reCAPTCHA ET les cookies de session.
    # Returns: Tuple (token, selenium_cookies_list)
    
    # Configuration Chrome
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    if profile_dir:
        chrome_options.add_argument('--user-data-dir=' + str(profile_dir))
    
    # Creer le driver
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        # Essayer avec webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError as e:
            raise RuntimeError(
                "webdriver-manager is not installed."
            ) from e
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("ChromeDriver installe automatiquement via webdriver-manager")

    try:
        try:
            driver.get("https://www.duelingbook.com/")  # Aller sur la home
        except Exception as e:
            print("ATTENTION: Probleme lors de la connexion: " + str(e))

        driver.get(replay_url) # Charger la page de replay
        
        print("Attente du chargement de reCAPTCHA...")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return typeof grecaptcha !== 'undefined'")
        )
        
        # Obtenir le token
        token = driver.execute_async_script("""
            var callback = arguments[arguments.length - 1];
            
            if (typeof grecaptcha === 'undefined') {
                callback(null);
                return;
            }
            
            grecaptcha.ready(function() {
                grecaptcha.execute('6LcjdkEgAAAAAKoEsPnPbSdjLkf4bLx68445txKj', {action: 'submit'})
                    .then(function(token) {
                        callback(token);
                    })
                    .catch(function(error) {
                        callback(null);
                    });
            });
        """)
        
        # Recuperer les cookies
        cookies = driver.get_cookies()
        try:
            cookie_names = [c.get("name") for c in cookies if isinstance(c, dict)]
            print("Cookies: " + ", ".join([str(n) for n in cookie_names if n]))
        except Exception:
            pass
        
        if token and len(token) > 50:
            print("Token reCAPTCHA obtenu! (longueur: " + str(len(token)) + ")")
            print("Cookies recuperes: " + str(len(cookies)) + " cookies")
            return token, cookies
        raise Exception("Impossible d'obtenir un token reCAPTCHA valide.")
    finally:
        try:
            driver.quit() # Fermer le navigateur
        except Exception:
            pass


def normalize_replay_url(url_or_id: str, *, strip_user_prefix: bool = True) -> str:
    # Accept:
    # - full replay URL: https://www.duelingbook.com/replay?id=745183-77512517
    # - view-replay URL: https://www.duelingbook.com/view-replay?id=...
    # - raw id: 745183-77512517 or 77512517
    s = (url_or_id or "").strip()
    if not s:
        raise ValueError("Empty replay identifier")

    # If it's in the form userId-duelId, prefer duelId-only by default.
    # This often avoids "must be logged in" restrictions for public replays.
    if strip_user_prefix and "-" in s and not s.startswith("http"):
        left, right = s.split("-", 1)
        if left.isdigit() and right.isdigit():
            s = right

    if s.startswith("http"):
        if "replay?id=" in s:
            return s
        if "view-replay?id=" in s:
            return s.replace("view-replay?id=", "replay?id=")
        # fallback: keep as-is
        return s
    return "https://www.duelingbook.com/replay?id=" + s


def get_match_data(url_id: str, *, profile_dir: str | None = None): # returns json containing match data
    try:
        import requests
    except ImportError as e:
        raise RuntimeError(
            "requests is not installed. Install dependencies with: pip install -r requirements.txt"
        ) from e
    
    replay_id, match = _parse_replay_id_and_match(url_id)
    url = "https://www.duelingbook.com/view-replay?id=" + replay_id
    if match:
        url += "&match=" + match

    
    # Obtenir le token reCAPTCHA et les cookies si non fournis
    recaptcha_token, cookies = get_recaptcha_token_and_cookies_with_selenium(url_id, profile_dir=profile_dir)
    
    # Donnees du formulaire
    form_data = {"token": recaptcha_token, "recaptcha_version": "3", "master": "2"}
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.duelingbook.com", "Referer": url_id}
    
    print("Requete a l'API DuelingBook...")
    print("URL: " + url)
    print("Replay ID: " + replay_id + (f" (match={match})" if match else ""))
    
    
    try:
        # Creer une session pour utiliser les cookies
        session = requests.Session()

        # Ajouter les cookies si disponibles
        if cookies: # cookies is a list
            for c in cookies:
                try:
                    name = c.get('name')
                    value = c.get('value')
                    domain = c.get('domain') or 'www.duelingbook.com'
                    path = c.get('path') or '/'
                    if name and value is not None:
                        session.cookies.set(name, value, domain=domain, path=path)
                except Exception:
                    pass
            print("Cookies de session ajoutes (" + str(len(cookies)) + " cookies)")
        
        # Faire la requete POST avec headers et cookies
        response = session.post(url, data=form_data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parser la reponse JSON
        data = response.json()
        
        # Verifier les erreurs
        if data.get("action") == "Error":
            error_msg = data.get("message", "Erreur inconnue")
            
            if "logged in" in error_msg.lower():
                print("")
                print("ATTENTION: Ce replay necessite une connexion.")
            
            raise Exception("Erreur API: " + str(error_msg))
        
        return data
    
    except requests.exceptions.RequestException as e:
        raise Exception("Erreur de requete: " + str(e))
    except json.JSONDecodeError as e:
        raise Exception("Erreur de parsing JSON: " + str(e))


def save_json(data, output_path): # Sauvegarde un dictionnaire (JSON) dans un fichier.
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


def read_links_from_file(path: Path) -> list[str]:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() in [".json"]:
        # Supports the JSON you export from the browser console (list of {"text": ..., "url": ...})
        # Also supports: list[str] where each string is an id/url.
        obj = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        links: list[str] = []

        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    s = _clean_link_value(item)
                    if s:
                        links.append(s)
                    continue
                if isinstance(item, dict):
                    url = _clean_link_value(item.get("url", ""))
                    if not url or url.upper() == "N/A":
                        continue
                    # keep anything that looks like a duelingbook replay link/id
                    if "duelingbook.com" in url and "replay" in url.lower():
                        links.append(url)
            return links

        if isinstance(obj, dict):
            # Best-effort: if user stored {"links": [...]} or {"replays": [...]}
            for k in ("links", "replays", "urls"):
                v = obj.get(k)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            s = _clean_link_value(item)
                            if s:
                                links.append(s)
                        elif isinstance(item, dict):
                            url = _clean_link_value(item.get("url", ""))
                            if url and url.upper() != "N/A":
                                links.append(url)
                    if links:
                        return links

        raise ValueError(f"Unsupported JSON structure in {path}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        try:
            import pandas as pd
        except ImportError as e:
            raise RuntimeError(
                "pandas is not installed. Install dependencies with: pip install -r requirements.txt"
            ) from e
        df = pd.read_excel(path)  # requires openpyxl for xlsx
        # take first column
        out: list[str] = []
        for x in df.iloc[:, 0].tolist():
            s = _clean_link_value(x)
            if s:
                out.append(s)
        return out

    if path.suffix.lower() in [".csv"]:
        try:
            import pandas as pd
        except ImportError as e:
            raise RuntimeError(
                "pandas is not installed. Install dependencies with: pip install -r requirements.txt"
            ) from e
        df = pd.read_csv(path)
        out: list[str] = []
        for x in df.iloc[:, 0].tolist():
            s = _clean_link_value(x)
            if s:
                out.append(s)
        return out

    # default: treat as text file (one link per line)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    for ln in lines:
        s = _clean_link_value(ln)
        if s:
            out.append(s)
    return out


def scrape_one(
    db_link: str,
    *,
    out_dir: Path,
    profile_dir: str | None = None,
    strip_user_prefix: bool = True,
) -> int:
    try:
        replay_url = normalize_replay_url(db_link, strip_user_prefix=strip_user_prefix)
        match_data = get_match_data(url_id=replay_url, profile_dir=profile_dir)
        out_dir = out_dir.expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / (get_replay_id(replay_url) + ".json")
        print("OK: JSON sauvegarde -> " + save_json(match_data, str(out_path)))
        return 0
    except Exception as e:
        print("")
        print("Erreur: " + str(e))
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch DuelingBook replay JSONs using Selenium (reCAPTCHA v3) and save them locally."
    )
    parser.add_argument(
        "--try-it-yourself",
        action="store_true",
        help=(
            "Convenience mode: read links from data/empty_match_data.csv, scrape into data/my_own_db_replays/, "
            "then build CSV + features and print model scores."
        ),
    )
    src = parser.add_mutually_exclusive_group(required=False)
    src.add_argument("--replay", type=str, help="Replay URL or id (e.g. 745183-77512517)")
    src.add_argument(
        "--links-file",
        type=Path,
        help="Path to .xlsx/.csv/.txt/.json containing replay links/ids (first column or one per line; json can be browser export)",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for JSON files")
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=None,
        help="Optional Chrome user-data-dir (NOT COMMITTED). Helps if some replays require login.",
    )
    parser.add_argument(
        "--keep-user-prefix",
        action="store_true",
        help="Do not strip userId from ids like '745183-77512517' (by default we keep only '77512517').",
    )
    parser.add_argument(
        "--run-ml",
        action="store_true",
        help="After scraping, build matches CSV + features and print baseline model scores.",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Do not stop the run if some replays fail (e.g. login required); continue and optionally run ML on successes.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Optional username to force into player1 when building the matches CSV.",
    )
    parser.add_argument(
        "--matches-csv",
        type=Path,
        default=DEFAULT_TRY_IT_YOURSELF_MATCHES_CSV,
        help="Where to write the built matches CSV (only used with --run-ml / --try-it-yourself).",
    )
    parser.add_argument(
        "--features-out",
        type=Path,
        default=DEFAULT_TRY_IT_YOURSELF_FEATURES_CSV,
        help="Where to write the built features CSV (only used with --run-ml / --try-it-yourself).",
    )
    args = parser.parse_args(argv)

    # Resolve preset mode
    if args.try_it_yourself:
        args.links_file = DEFAULT_TRY_IT_YOURSELF_LINKS
        args.out_dir = DEFAULT_TRY_IT_YOURSELF_REPLAYS_DIR
        args.run_ml = True

    if not (args.replay or args.links_file):
        parser.error("one of the arguments --replay --links-file is required (or use --try-it-yourself)")

    links: Iterable[str]
    if args.replay:
        links = [args.replay]
    else:
        links = read_links_from_file(args.links_file)

    failures = 0
    successes = 0
    for link in links:
        rc = scrape_one(
            link,
            out_dir=args.out_dir,
            profile_dir=args.profile_dir,
            strip_user_prefix=not args.keep_user_prefix,
        )
        if rc == 0:
            successes += 1
        else:
            failures += 1

    if failures:
        print(f"Done with {failures} failure(s).")
        if not args.continue_on_failure and not args.run_ml:
            return 1
        if not args.continue_on_failure and args.run_ml and successes == 0:
            return 1

    if failures == 0:
        print("Done with 0 failures.")
    else:
        print(f"Continuing with {successes} success(es) despite failures.")

    # Optional: run offline ML pipeline on freshly scraped replays
    if args.run_ml:
        if successes == 0:
            print("No replay JSONs were saved successfully; skipping ML.")
            return 1
        try:
            from get_csv_from_json import build_matches_dataframe
            from ML_for_YGO import build_features, load_dataset, train_and_score_models
        except Exception as e:
            raise RuntimeError(
                "Unable to import pipeline modules (get_csv_from_json / ML_for_YGO). "
                "Make sure you're running from the repo and dependencies are installed."
            ) from e

        replays_dir = args.out_dir.expanduser().resolve()
        df = build_matches_dataframe(replays_dir, data_provider_username=args.provider)
        args.matches_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.matches_csv, index=False)
        print(f"✅ Matches CSV saved to: {args.matches_csv} (rows={len(df)})")

        dataset = load_dataset(args.matches_csv)

        # In try-it-yourself mode, we want this to work on arbitrary replays, so we disable
        # the deck-specific filter (if supported by ML_for_YGO.py).
        try:
            X, y = build_features(dataset, replays_dir, filter_wrong_deck=False)  # type: ignore[call-arg]
        except TypeError:
            X, y = build_features(dataset, replays_dir)

        args.features_out.parent.mkdir(parents=True, exist_ok=True)
        X.to_csv(args.features_out, index=False)
        print(f"✅ Features CSV saved to: {args.features_out} (shape={X.shape})")

        if len(X) == 0:
            print("⚠️ No samples available after feature building; skipping model training.")
            return 0

        scores = train_and_score_models(X, y)
        print("Scores:")
        for k, v in scores.items():
            print(f"  - {k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())