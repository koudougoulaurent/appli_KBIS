@echo off
echo Demarrage de l'application de gestion immobiliere
echo.

REM Verifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo L'environnement virtuel n'existe pas. Veuillez d'abord executer install.bat
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

REM Demarrer l'application
echo Demarrage de l'application...
python manage.py runserver
if %errorlevel% neq 0 (
    echo Erreur lors du demarrage de l'application.
    pause
    exit /b 1
)

echo.
echo L'application est maintenant accessible a l'adresse http://127.0.0.1:8000/