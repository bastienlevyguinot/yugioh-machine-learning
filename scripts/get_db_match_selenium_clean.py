"""
Script pour recuperer les donnees d'un match DuelingBook via l'API avec Selenium.
Utilise Selenium pour obtenir un token reCAPTCHA valide automatiquement.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import json
import sys

DEFAULT_OUT_DIR = Path("data/db_replays")

def get_replay_id(url_id):
    return url_id.split("=")[1]

def get_recaptcha_token_and_cookies_with_selenium(replay_url: str, *, profile_dir: str | None = None):
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        raise RuntimeError(
            "Selenium is not installed. Install dependencies with: pip install -r requirements.txt"
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
                "webdriver-manager is not installed. Install dependencies with: pip install -r requirements.txt"
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


def normalize_replay_url(url_or_id: str) -> str:
    # Accept:
    # - full replay URL: https://www.duelingbook.com/replay?id=745183-77512517
    # - view-replay URL: https://www.duelingbook.com/view-replay?id=...
    # - raw id: 745183-77512517 or 77512517
    s = (url_or_id or "").strip()
    if not s:
        raise ValueError("Empty replay identifier")
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
    
    replay_id = url_id.split("=")[1]
    url = "https://www.duelingbook.com/view-replay?id=" + replay_id

    
    # Obtenir le token reCAPTCHA et les cookies si non fournis
    recaptcha_token, cookies = get_recaptcha_token_and_cookies_with_selenium(url_id, profile_dir=profile_dir)
    
    # Donnees du formulaire
    form_data = {"token": recaptcha_token, "recaptcha_version": "3", "master": "2"}
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.duelingbook.com", "Referer": url_id}
    
    print("Requete a l'API DuelingBook...")
    print("URL: " + url)
    print("Replay ID: " + replay_id)
    
    
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

    if path.suffix.lower() in [".xlsx", ".xls"]:
        try:
            import pandas as pd
        except ImportError as e:
            raise RuntimeError(
                "pandas is not installed. Install dependencies with: pip install -r requirements.txt"
            ) from e
        df = pd.read_excel(path)  # requires openpyxl for xlsx
        # take first column
        return [str(x) for x in df.iloc[:, 0].tolist() if str(x).strip()]

    if path.suffix.lower() in [".csv"]:
        try:
            import pandas as pd
        except ImportError as e:
            raise RuntimeError(
                "pandas is not installed. Install dependencies with: pip install -r requirements.txt"
            ) from e
        df = pd.read_csv(path)
        return [str(x) for x in df.iloc[:, 0].tolist() if str(x).strip()]

    # default: treat as text file (one link per line)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return [ln.strip() for ln in lines if ln.strip()]


def scrape_one(db_link: str, *, out_dir: Path, profile_dir: str | None = None) -> int:
    try:
        replay_url = normalize_replay_url(db_link)
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
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--replay", type=str, help="Replay URL or id (e.g. 745183-77512517)")
    src.add_argument("--links-file", type=Path, help="Path to .xlsx/.csv/.txt containing replay links/ids (first column or one per line)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for JSON files")
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=None,
        help="Optional Chrome user-data-dir (NOT COMMITTED). Helps if some replays require login.",
    )
    args = parser.parse_args(argv)

    links: Iterable[str]
    if args.replay:
        links = [args.replay]
    else:
        links = read_links_from_file(args.links_file)

    failures = 0
    for link in links:
        failures += 1 if scrape_one(link, out_dir=args.out_dir, profile_dir=args.profile_dir) != 0 else 0

    if failures:
        print(f"Done with {failures} failure(s).")
        return 1
    print("Done with 0 failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())