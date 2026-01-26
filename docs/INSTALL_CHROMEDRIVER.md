# Installation de ChromeDriver (sans Homebrew)

## Option 1 : Installer Homebrew d'abord (recommandé)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Puis :
```bash
brew install chromedriver
```

## Option 2 : Télécharger ChromeDriver manuellement

### Étape 1 : Vérifier votre version de Chrome
1. Ouvrez Chrome
2. Allez dans Chrome > À propos de Google Chrome
3. Notez le numéro de version (ex: 120.0.6099.109)

### Étape 2 : Télécharger ChromeDriver
1. Allez sur : https://chromedriver.chromium.org/downloads
2. Téléchargez la version correspondante à votre Chrome
3. Décompressez le fichier

### Étape 3 : Installer ChromeDriver
```bash
# Déplacer chromedriver vers un dossier dans votre PATH
sudo mv ~/Downloads/chromedriver /usr/local/bin/

# Rendre exécutable
sudo chmod +x /usr/local/bin/chromedriver
```

### Étape 4 : Vérifier
```bash
chromedriver --version
```

## Option 3 : Utiliser webdriver-manager (automatique)

Installer webdriver-manager qui télécharge automatiquement ChromeDriver :

```bash
pip install webdriver-manager
```

Puis modifier le script pour utiliser webdriver-manager au lieu de ChromeDriver direct.

