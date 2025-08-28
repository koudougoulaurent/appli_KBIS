@echo off
echo Initialisation de la base de donnees et creation du superutilisateur
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

REM Executer le script d'initialisation
echo Execution du script d'initialisation...
python init_db.py
if %errorlevel% neq 0 (
    echo Erreur lors de l'execution du script d'initialisation.
    pause
    exit /b 1
)

echo.
echo Initialisation terminee avec succes !
pause