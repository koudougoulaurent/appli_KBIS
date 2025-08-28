# Script d'installation automatique des dépendances

## Description
Ce script facilite l'installation automatique des dépendances nécessaires pour exécuter l'application de gestion immobilière.

## Script d'installation

### Pour Windows (install.bat)

```batch
@echo off
echo Installation des dependances pour l'application de gestion immobiliere
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installe. Veuillez installer Python 3.8 ou superieur.
    pause
    exit /b 1
)

REM Creer un environnement virtuel
echo Creation de l'environnement virtuel...
python -m venv venv
if %errorlevel% neq 0 (
    echo Erreur lors de la creation de l'environnement virtuel.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Erreur lors de l'activation de l'environnement virtuel.
    pause
    exit /b 1
)

REM Installer les dependances
echo Installation des dependances...
pip install Django>=4.2.7
pip install django-bootstrap5>=2.0

echo.
echo Installation terminee avec succes !
echo Pour activer l'environnement virtuel, executez : venv\Scripts\activate.bat
pause
```

### Pour macOS/Linux (install.sh)

```bash
#!/bin/bash

echo "Installation des dependances pour l'application de gestion immobiliere"
echo

# Verifier si Python est installe
if ! command -v python3 &> /dev/null
then
    echo "Python n'est pas installe. Veuillez installer Python 3.8 ou superieur."
    exit 1
fi

# Creer un environnement virtuel
echo "Creation de l'environnement virtuel..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Erreur lors de la creation de l'environnement virtuel."
    exit 1
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel."
    exit 1
fi

# Installer les dependances
echo "Installation des dependances..."
pip install Django>=4.2.7
pip install django-bootstrap5>=2.0

echo
echo "Installation terminee avec succes !"
echo "Pour activer l'environnement virtuel, executez : source venv/bin/activate"
```

## Utilisation

### Windows
1. Enregistrez le contenu du script Windows dans un fichier `install.bat`
2. Double-cliquez sur `install.bat` ou exécutez-le depuis l'invite de commandes

### macOS/Linux
1. Enregistrez le contenu du script macOS/Linux dans un fichier `install.sh`
2. Rendez le script exécutable : `chmod +x install.sh`
3. Exécutez le script : `./install.sh`

## Prochaines étapes

Après avoir exécuté le script d'installation, vous pouvez suivre les instructions du fichier README.md pour:

1. Configurer la base de données
2. Créer un superutilisateur
3. Exécuter l'application