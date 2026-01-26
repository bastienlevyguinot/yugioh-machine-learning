"""
Script pour recuperer les donnees d'un match DuelingBook via l'API avec Selenium.
Utilise Selenium pour obtenir un token reCAPTCHA valide automatiquement.
"""

from locale import D_FMT
import requests
import json
import sys
import pandas as pd

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("ERREUR: Selenium n'est pas installe.")
    print("Installez-le avec: pip install selenium")
    sys.exit(1)

DEFAULT_PROFILE_DIR = "/Users/BastienLevy-Guinot/Desktop/chrome_profile_duelingbook"
DEFAULT_OUT_PATH_PREFIX = "/Users/BastienLevy-Guinot/Desktop/db_replays/"
DEFAULT_EXCEL_FILE = "db_links_RB_Amir_Salhi.xlsx"

def get_replay_id(url_id):
    return url_id.split("=")[1]

def get_recaptcha_token_and_cookies_with_selenium(replay_url): 

    # Utilise Selenium pour obtenir un token reCAPTCHA ET les cookies de session.
    # Returns: Tuple (token, selenium_cookies_list)
    
    # Configuration Chrome
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    if DEFAULT_PROFILE_DIR: 
        chrome_options.add_argument('--user-data-dir=' + str(DEFAULT_PROFILE_DIR))
    
    # Creer le driver
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        # Essayer avec webdriver-manager
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("ChromeDriver installe automatiquement via webdriver-manager")

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
    else:
        raise Exception("Impossible d'obtenir un token reCAPTCHA valide.")

    driver.quit() # Fermer le navigateur



def get_match_data(url_id): # returns json containing match data
    
    replay_id = url_id.split("=")[1]
    url = "https://www.duelingbook.com/view-replay?id=" + replay_id

    
    # Obtenir le token reCAPTCHA et les cookies si non fournis
    recaptcha_token, cookies = get_recaptcha_token_and_cookies_with_selenium(url_id)
    
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

def main(db_link):
    try:
        match_data = get_match_data(url_id=db_link)
        print("OK: JSON sauvegarde -> " + save_json(match_data, DEFAULT_OUT_PATH_PREFIX + get_replay_id(db_link) + ".json"))
        return 0
    except Exception as e:
        print("")
        print("Erreur: " + str(e))
        return 1


df = pd.read_excel(DEFAULT_EXCEL_FILE) # read excel file
my_list = df.iloc[:, 0].tolist()
for url_id in my_list:
    main(url_id)