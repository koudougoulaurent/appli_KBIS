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
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erreur lors de l'installation des dependances.
    pause
    exit /b 1
)

echo.
echo Installation terminee avec succes !
echo Pour activer l'environnement virtuel, executez : venv\Scripts\activate.bat
echo Pour demarrer l'application, executez : python manage.py runserver
pause