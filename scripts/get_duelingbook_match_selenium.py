"""
Script pour recuperer les donnees d'un match DuelingBook via l'API avec Selenium.
Utilise Selenium pour obtenir un token reCAPTCHA valide automatiquement.
"""


import requests
import json
import sys
from urllib.parse import urlparse, parse_qs
import time
import os

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("ERREUR: Selenium n'est pas installe.")
    print("Installez-le avec: pip install selenium")
    sys.exit(1)

# ===========================
# DEFAULTS (mode bouton "Run")
# ===========================
# Si tu cliques "Run" dans Cursor sans arguments, le script utilisera ces valeurs.
# Modifie-les ici selon ton besoin.
DEFAULT_REPLAY = "745183-77512517"  # ou une URL replay complete
DEFAULT_USERNAME = "MonPseaudo"
DEFAULT_PASSWORD = ""  # optionnel: mets ton mot de passe ici (sinon laisse vide)
DEFAULT_PROFILE_DIR = "/Users/BastienLevy-Guinot/Desktop/chrome_profile_duelingbook"
DEFAULT_OUT_PATH = "/Users/BastienLevy-Guinot/Desktop/match_data.json"
DEFAULT_HEADLESS = False

def _is_logged_in(driver):
    # Est-ce que ce Chrome est déjà connecté à DuelingBook ?
    # Cherche un lien/bouton logout, ou un indice dans le HTML.
    try:
        # if driver.find_elements(By.CSS_SELECTOR, "a[href*='logout' i], button[onclick*='logout' i]"):
        #     return True
        src = (driver.page_source or "").lower()
        if "logout" in src or "log out" in src:
            return True
    except Exception:
        pass
    return False

# =============== Fonction désactivée ===============
def _find_login_fields_in_context(driver):
    """
    Essaie de trouver les champs username/password dans le contexte courant (default content ou iframe).
    Retourne (user_el, pass_el) ou (None, None).
    """
    # DESACTIVE (mis "en commentaire") pour debug: on renvoie toujours (None, None).
    # Attention: ça empêche l'auto-login de fonctionner, car le script ne trouvera jamais les champs.
    return None, None

    """
    Ancienne logique (gardee ici en commentaire):

    user_el = None
    pass_el = None

    # Password: souvent le plus fiable
    try:
        pass_candidates = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        print("Pass candidates: ", pass_candidates)
        if pass_candidates:
            pass_el = pass_candidates[0]
            print("Pass el: ", pass_el)
    except Exception:
        pass_el = None

    # Username/email: beaucoup de variantes
    for by, val in [
        (By.NAME, "username"),
        (By.NAME, "user"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.CSS_SELECTOR, "input[name='user']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[id='username']"),
        (By.CSS_SELECTOR, "input[id='user']"),
        (By.CSS_SELECTOR, "input[id*='user' i]"),
        (By.XPATH, "//input[contains(translate(@placeholder,'USERNAMEEMAIL','usernameemail'),'user') or contains(translate(@placeholder,'USERNAMEEMAIL','usernameemail'),'email')]"),
        (By.XPATH, "//input[contains(translate(@aria-label,'USERNAMEEMAIL','usernameemail'),'user') or contains(translate(@aria-label,'USERNAMEEMAIL','usernameemail'),'email')]"),
    ]:
        try:
            els = driver.find_elements(by, val)
            if els:
                user_el = els[0]
                break
        except Exception:
            pass

    # Fallback: si on a un password, prendre le premier input texte visible
    if pass_el and (not user_el):
        try:
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type])")
            if text_inputs:
                user_el = text_inputs[0]
        except Exception:
            pass

    if user_el and pass_el:
        return user_el, pass_el
    return None, None
    """
# =============== Fonction désactivée ===============


# =============== Fonction désactivée ===============
def _find_login_fields_anywhere(driver):
    """
    Cherche les champs login dans la page, y compris dans les iframes.
    Retourne (user_el, pass_el, frame_idx) où frame_idx=None si default content.
    """
    # DESACTIVE (mis "en commentaire") pour debug: on renvoie toujours (None, None, None).
    # Attention: ça empêche l'auto-login de fonctionner, car le script ne cherchera jamais les champs (même dans les iframes).
    return None, None, None

    """
    Ancienne logique (gardee ici en commentaire):

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    u, p = _find_login_fields_in_context(driver)
    if u and p:
        return u, p, None

    # Essayer dans les iframes (certaines pages utilisent des embeds/modals)
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
    except Exception:
        iframes = []

    for idx, fr in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(fr)
            u, p = _find_login_fields_in_context(driver)
            if u and p:
                return u, p, idx
        except Exception:
            pass

    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    return None, None, None
    """
# =============== Fonction désactivée ===============

# =============== Fonction désactivée ===============
def _debug_list_inputs(driver, max_items=20):
    """
    Affiche quelques inputs pour comprendre pourquoi les selecteurs ne matchent pas.
    """
    # DESACTIVE (mis "en commentaire") pour debug: ne fait rien.
    return

    """
    Ancienne logique (gardee ici en commentaire):

    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
    except Exception:
        inputs = []
    print("DEBUG: inputs detectes (max " + str(max_items) + "): " + str(len(inputs)))
    shown = 0
    for el in inputs:
        if shown >= max_items:
            break
        try:
            t = el.get_attribute("type")
            n = el.get_attribute("name")
            i = el.get_attribute("id")
            ph = el.get_attribute("placeholder")
            al = el.get_attribute("aria-label")
            print("  - type=" + str(t) + " name=" + str(n) + " id=" + str(i) + " placeholder=" + str(ph) + " aria-label=" + str(al))
            shown += 1
        except Exception:
            pass
    """
# =============== Fonction désactivée ===============

def extract_ids_from_input(input_str):
    """
    Extrait duelId et userId depuis une URL ou un ID.
    
    Formats acceptes:
    - URL: https://www.duelingbook.com/replay?id=745183-77512517
    - ID avec userId: 745183-77512517
    - ID seul: 77512517
    """
    # Si c'est une URL
    if input_str.startswith('http'):
        parsed = urlparse(input_str)
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            id_str = query_params['id'][0]
        else:
            raise ValueError("URL invalide: pas de parametre 'id' trouve")
    else:
        # Sinon, c'est directement l'ID
        id_str = input_str
    
    # Parser l'ID
    if '-' in id_str:
        parts = id_str.split('-')
        user_id = int(parts[0])
        duel_id = int(parts[1])
    else:
        user_id = None
        duel_id = int(id_str)
    
    return duel_id, user_id


# =============== Fonction désactivée ===============
def get_recaptcha_token_with_selenium(replay_url):
    # DESACTIVE: cette fonction n'est plus utilisée (remplacée par get_recaptcha_token_and_cookies_with_selenium).
    return None
    
    # Ancienne logique (gardée ici en commentaire):
    #
    # Utilise Selenium pour obtenir un token reCAPTCHA valide.
    #
    # print("Ouverture du navigateur avec Selenium...")
    #
    # # Configuration Chrome
    # chrome_options = Options()
    # # chrome_options.add_argument('--headless')  # Desactive pour debug (activer pour mode invisible)
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    #
    # # Creer le driver
    # try:
    #     # Essayer d'abord avec ChromeDriver standard
    #     driver = webdriver.Chrome(options=chrome_options)
    # except Exception as e:
    #     # Si echec, essayer avec webdriver-manager (si installe)
    #     try:
    #         from webdriver_manager.chrome import ChromeDriverManager
    #         from selenium.webdriver.chrome.service import Service
    #         service = Service(ChromeDriverManager().install())
    #         driver = webdriver.Chrome(service=service, options=chrome_options)
    #         print("ChromeDriver installe automatiquement via webdriver-manager")
    #     except ImportError:
    #         print("ERREUR: Impossible de creer le driver Chrome.")
    #         print("Option 1: Installez ChromeDriver manuellement")
    #         print("  - Telechargez depuis: https://chromedriver.chromium.org/downloads")
    #         print("  - Placez-le dans /usr/local/bin/")
    #         print("")
    #         print("Option 2: Installez webdriver-manager (recommandé)")
    #         print("  pip install webdriver-manager")
    #         print("")
    #         print("Erreur: " + str(e))
    #         raise
    #     except Exception as e2:
    #         print("ERREUR: Impossible de creer le driver Chrome.")
    #         print("Erreur: " + str(e2))
    #         raise
    #
    # try:
    #     print("Chargement de la page: " + replay_url)
    #     driver.get(replay_url)
    #
    #     # Attendre que reCAPTCHA soit charge
    #     print("Attente du chargement de reCAPTCHA...")
    #     WebDriverWait(driver, 15).until(
    #         lambda d: d.execute_script("return typeof grecaptcha !== 'undefined'")
    #     )
    #
    #     print("reCAPTCHA detecte, generation du token...")
    #
    #     # Executer grecaptcha.execute() pour obtenir le token
    #     # Site key de DuelingBook: 6LcjdkEgAAAAAKoEsPnPbSdjLkf4bLx68445txKj
    #     token = driver.execute_async_script('''
    #         var callback = arguments[arguments.length - 1];
    #
    #         if (typeof grecaptcha === 'undefined') {
    #             callback(null);
    #             return;
    #         }
    #
    #         grecaptcha.ready(function() {
    #             grecaptcha.execute('6LcjdkEgAAAAAKoEsPnPbSdjLkf4bLx68445txKj', {action: 'submit'})
    #                 .then(function(token) {
    #                     callback(token);
    #                 })
    #                 .catch(function(error) {
    #                     console.error('reCAPTCHA error:', error);
    #                     callback(null);
    #                 });
    #         });
    #     ''')
    #
    #     if token and len(token) > 50:  # Les tokens reCAPTCHA sont longs
    #         print("Token reCAPTCHA obtenu avec succes! (longueur: " + str(len(token)) + ")")
    #         return token
    #     else:
    #         print("ATTENTION: Token invalide ou vide.")
    #         print("Tentative alternative...")
    #
    #         # Attendre un peu plus et reessayer
    #         time.sleep(3)
    #         token = driver.execute_async_script('''
    #             var callback = arguments[arguments.length - 1];
    #
    #             if (typeof grecaptcha === 'undefined') {
    #                 callback(null);
    #                 return;
    #             }
    #
    #             grecaptcha.ready(function() {
    #                 grecaptcha.execute('6LcjdkEgAAAAAKoEsPnPbSdjLkf4bLx68445txKj', {action: 'submit'})
    #                     .then(function(token) {
    #                         callback(token);
    #                     })
    #                     .catch(function(error) {
    #                         callback(null);
    #                     });
    #             });
    #         ''')
    #
    #         if token and len(token) > 50:
    #             print("Token obtenu lors de la deuxieme tentative!")
    #             return token
    #         else:
    #             raise Exception("Impossible d'obtenir un token reCAPTCHA valide. Le site peut detecter l'automation.")
    #
    # except Exception as e:
    #     print("Erreur lors de la recuperation du token: " + str(e))
    #     raise
    #
    # finally:
    #     driver.quit()
    #     print("Navigateur ferme.")
# =============== Fonction désactivée ===============


def get_recaptcha_token_and_cookies_with_selenium(
    replay_url,
    username="[TRINITY] WhiteDevil",
    password="",
    user_data_dir=None,
    headless=False
):
    """
    Utilise Selenium pour obtenir un token reCAPTCHA ET les cookies de session.
    Si username/password sont fournis, se connecte d'abord.
    
    Args:
        replay_url: URL de la page de replay
        username: Nom d'utilisateur DuelingBook (optionnel)
        password: Mot de passe (optionnel)
        user_data_dir: Dossier de profil Chrome a reutiliser (optionnel)
        pause_for_manual_login: Si True, ouvre Chrome et attend que vous vous connectiez manuellement (sans mot de passe dans le code)
        headless: Si True, lance Chrome en mode invisible (deconseille si pause_for_manual_login)
    
    Returns:
        Tuple (token, selenium_cookies_list)
    """
    print("Ouverture du navigateur avec Selenium...")
    
    # Configuration Chrome
    chrome_options = Options()
    if headless: # Jamais cette condition n'est vraie car headless est False
        # Mode invisible (peut augmenter la detection d'automation selon les sites)
        print("HEADLESS MODE")
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    if user_data_dir: 
        chrome_options.add_argument('--user-data-dir=' + str(user_data_dir))
    
    # Creer le driver
    try:
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            # Essayer avec webdriver-manager
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("ChromeDriver installe automatiquement via webdriver-manager")
    except Exception as e:
        print("ERREUR: Impossible de creer le driver Chrome.")
        print("Erreur: " + str(e))
        raise
    
    try:
        # Auto-login uniquement: on ignore le mode "manual login" si jamais il est passe.

        # Se connecter si username fourni (password optionnel)
        if username is not None:
            print("Connexion a DuelingBook...")
            try:
                # Aller sur la home
                driver.get("https://www.duelingbook.com/")
                time.sleep(2)

                # Si deja connecte (ex: profil chrome reutilise), on ne fait rien
                if _is_logged_in(driver):
                    print("Deja connecte (detecte via logout).")
                
                # _is_logged_in(driver) est toujours vraie, donc on ne passe pas dans le else
                """    
                else:
                    # Aller directement sur la page login (le plus stable)
                    driver.get("https://www.duelingbook.com/login")
                    time.sleep(2)

                    # Trouver les champs (dans page ou iframes)
                    user_el, pass_el, frame_idx = _find_login_fields_anywhere(driver)

                    if user_el and pass_el:
                        try:
                            user_el.clear()
                        except Exception:
                            pass
                        user_el.send_keys(username)
                        try:
                            pass_el.clear()
                        except Exception:
                            pass
                        if password is None:
                            password = ""
                        pass_el.send_keys(password)

                        # Soumettre (dans le contexte courant)
                        submitted = False
                        for by, val in [
                            (By.CSS_SELECTOR, "button[type='submit']"),
                            (By.CSS_SELECTOR, "input[type='submit']"),
                            (By.XPATH, "//button[contains(., 'Login') or contains(., 'Sign in') or contains(., 'Sign In') or contains(., 'Se connecter')]"),
                            (By.XPATH, "//input[@type='submit']"),
                        ]:
                            try:
                                els = driver.find_elements(by, val)
                                if els:
                                    els[0].click()
                                    submitted = True
                                    break
                            except Exception:
                                pass

                        # Retourner au contenu principal si on etait dans une iframe
                        try:
                            driver.switch_to.default_content()
                        except Exception:
                            pass

                        if submitted:
                            # Attendre un petit peu que la session s'etablisse
                            time.sleep(3)
                            # Aller sur la home et verifier
                            driver.get("https://www.duelingbook.com/")
                            time.sleep(2)
                            if _is_logged_in(driver):
                                print("Connexion reussie (logout detecte).")
                            else:
                                print("ATTENTION: Login soumis mais pas de preuve de connexion (logout non detecte).")
                        else:
                            print("ATTENTION: Bouton submit introuvable, continuation...")
                    else:
                        print("ATTENTION: Champs login introuvables, continuation...")
                        print("DEBUG: url=" + str(getattr(driver, "current_url", "")))
                        try:
                            print("DEBUG: title=" + str(driver.title))
                        except Exception:
                            pass
                        _debug_list_inputs(driver)
                """
            except Exception as e:
                print("ATTENTION: Probleme lors de la connexion: " + str(e))
                print("Continuation sans connexion...")
        
        # Charger la page de replay
        print("Chargement de la page: " + replay_url)
        driver.get(replay_url)
        
        # Attendre que la page charge, pas besoin de le faire car nous attendons 15 secondes avant de generer le token reCAPTCHA
        # print("Attente du chargement de la page...")
        # time.sleep(5)
        
        # Attendre que reCAPTCHA soit charge
        print("Attente du chargement de reCAPTCHA...")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return typeof grecaptcha !== 'undefined'")
        )
        
        print("reCAPTCHA detecte, generation du token...")
        
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
    
    finally:
        driver.quit()
        print("Navigateur ferme.")


def get_match_data(
    duel_id,
    user_id=None,
    recaptcha_token=None,
    cookies=None,
    username=None,
    password=None,
    user_data_dir=None,
    headless=False
):
    """
    Fait une requete a l'API DuelingBook pour recuperer les donnees du match.
    
    Args:
        duel_id: ID du duel
        user_id: ID de l'utilisateur (optionnel)
        recaptcha_token: Token reCAPTCHA (optionnel, sera obtenu avec Selenium si None)
        cookies: Dictionnaire de cookies (optionnel, sera obtenu avec Selenium si None)
        username: Nom d'utilisateur pour se connecter (optionnel)
        password: Mot de passe pour se connecter (optionnel)
    
    Returns:
        Dictionnaire JSON contenant les donnees du match
    """
    base_url = "https://www.duelingbook.com/"
    
    # Construire l'ID du replay
    if user_id:
        replay_id = str(user_id) + "-" + str(duel_id)
    else:
        replay_id = str(duel_id)
    
    url = base_url + "view-replay?id=" + replay_id
    replay_url = base_url + "replay?id=" + replay_id
    
    # Obtenir le token reCAPTCHA et les cookies si non fournis
    print("Obtention du token reCAPTCHA et des cookies avec Selenium...")
    recaptcha_token, cookies = get_recaptcha_token_and_cookies_with_selenium(
        replay_url,
        username=username,
        password=password,
        user_data_dir=user_data_dir,
        headless=headless
    )
    
    # Donnees du formulaire
    form_data = {
        "token": recaptcha_token,  # Token reCAPTCHA obtenu
        "recaptcha_version": "3",
        "master": "2"  # Niveau master (2 = acces complet)
    }
    
    # Headers pour simuler un navigateur
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.duelingbook.com",
        "Referer": replay_url
    }
    
    print("Requete a l'API DuelingBook...")
    print("URL: " + url)
    print("Replay ID: " + replay_id)
    
    try:
        # Creer une session pour utiliser les cookies
        session = requests.Session()

        print(type(cookies))
        
        # Ajouter les cookies si disponibles
        if cookies:
            # cookies peut etre une liste Selenium (dicts avec domain/path), ou un dict simple name->value
            if isinstance(cookies, list):
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
                # ================ elif inutile
                """
            elif isinstance(cookies, dict): # cookies est une liste
                for name, value in cookies.items():
                    session.cookies.set(name, value, domain='www.duelingbook.com', path='/')
                print("Cookies de session ajoutes (" + str(len(cookies)) + " cookies)")
                """
                # ================ elif inutile
        
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
                print("Options:")
                print("  1. Verifie ton username/password (auto-login) ou passe --username/--password")
                print("  2. Utilise --profile pour reutiliser un profil Chrome deja connecte")
                print("  3. Essaye un autre replay public")
            
            raise Exception("Erreur API: " + str(error_msg))
        
        return data
    
    except requests.exceptions.RequestException as e:
        raise Exception("Erreur de requete: " + str(e))
    except json.JSONDecodeError as e:
        raise Exception("Erreur de parsing JSON: " + str(e))


def save_json(data, output_path):
    """
    Sauvegarde un dictionnaire (JSON) dans un fichier.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


def main(input_str,argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Mode bouton "Run" (aucun argument): on utilise les valeurs par defaut ecrites dans le code.
    if not argv:
        out_path = DEFAULT_OUT_PATH
        profile_dir = DEFAULT_PROFILE_DIR
        username = DEFAULT_USERNAME
        password = DEFAULT_PASSWORD
        # On continue ensuite comme un run normal.
    """
    else: 
        if argv[0] in ["-h", "--help"]:
            _print_usage()
            return 0

        input_str = argv[0]

        out_path = None
        profile_dir = None
        headless = False
        username = None
        password = None

        i = 1
        while i < len(argv):
            a = argv[i]
            if a == "--out" and i + 1 < len(argv):
                out_path = argv[i + 1]
                i += 2
            elif a == "--profile" and i + 1 < len(argv):
                profile_dir = argv[i + 1]
                i += 2
            elif a == "--headless":
                headless = True
                i += 1
            elif a == "--username" and i + 1 < len(argv):
                username = argv[i + 1]
                i += 2
            elif a == "--password" and i + 1 < len(argv):
                password = argv[i + 1]
                i += 2
            else:
                print("Argument inconnu: " + str(a))
                _print_usage()
                return 2
        """

    # IDs
    duel_id, user_id = extract_ids_from_input(input_str)

    try:
        match_data = get_match_data(
            duel_id=duel_id,
            user_id=user_id,
            username=username,
            password=password,
            user_data_dir=profile_dir,
            headless=False
        )
        save_json(match_data, out_path)
        print("OKAYYY")
        print("")
        print("OK: JSON sauvegarde -> " + out_path)
        return 0
    except Exception as e:
        print("")
        print("Erreur: " + str(e))
        return 1



if __name__ == "__main__":
    raise SystemExit(main("https://www.duelingbook.com/replay?id=745183-77512517"))