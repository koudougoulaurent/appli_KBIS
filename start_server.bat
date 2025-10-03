@echo off
echo 🚀 Démarrage du serveur KBIS avec système de téléphone Afrique de l'Ouest
echo ========================================================================

REM Configuration de l'environnement Django
set DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings

echo 📱 Système de téléphone configuré pour 15 pays d'Afrique de l'Ouest
echo 🌍 Pays supportés: Bénin, Sénégal, Côte d'Ivoire, Nigeria, Ghana, etc.
echo.

echo 🔧 Application des migrations...
python manage.py migrate

echo.
echo 🌐 Démarrage du serveur de développement...
echo 📍 URL: http://127.0.0.1:8000/
echo 📱 Formulaire locataire: http://127.0.0.1:8000/proprietes/locataires/ajouter/
echo.

python manage.py runserver

pause
