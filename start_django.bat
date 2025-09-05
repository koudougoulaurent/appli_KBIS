@echo off
echo 🚀 Démarrage du serveur Django GESTIMMOB
echo ==========================================

REM Aller au bon dossier
cd /d "C:\Users\GAMER\Desktop\gestionImo"

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Aller dans le dossier Django
cd appli_KBIS

REM Vérifier la configuration
echo 🔍 Vérification de la configuration...
python manage.py check
if errorlevel 1 (
    echo ❌ Erreurs de configuration détectées
    pause
    exit /b 1
)

REM Appliquer les migrations si nécessaire
echo 📦 Application des migrations...
python manage.py migrate

REM Collecter les fichiers statiques
echo 📁 Collection des fichiers statiques...
python manage.py collectstatic --noinput

REM Démarrer le serveur
echo 🌐 Démarrage du serveur sur http://127.0.0.1:8000/
echo 🛑 Pour arrêter le serveur: Ctrl+C
echo ==========================================
python manage.py runserver 127.0.0.1:8000

pause
