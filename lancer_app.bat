@echo off
echo 🚀 Lancement de l'application Django...
echo 📍 URL: http://127.0.0.1:8000/
echo 🛑 Arrêter avec Ctrl+C
echo ==================================================

set DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings
python manage.py runserver 8000

pause
