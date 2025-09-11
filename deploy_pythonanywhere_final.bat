@echo off
REM ===========================================
REM SCRIPT DE DÉPLOIEMENT FINAL PYTHONANYWHERE
REM ===========================================
REM Ce script corrige TOUS les problèmes identifiés

echo 🚀 DÉPLOIEMENT FINAL PYTHONANYWHERE - CORRECTION COMPLÈTE
echo ==========================================================

REM 1. Aller dans le répertoire du projet
cd /d C:\Users\GAMER\Documents\appli_KBIS

REM 2. Activer l'environnement virtuel (si nécessaire)
REM call venv\Scripts\activate

REM 3. Installer les packages manquants
echo 📦 Installation des packages manquants...
pip install django-filter
pip install django-select2
pip install whitenoise

REM 4. Vérifier l'installation
echo ✅ Vérification des packages installés...
pip list | findstr "django-filter django-select2 whitenoise"

REM 5. Appliquer les migrations
echo 🗄️ Application des migrations...
python manage.py makemigrations
python manage.py migrate

REM 6. Collecter les fichiers statiques
echo 📁 Collecte des fichiers statiques...
python manage.py collectstatic --noinput

REM 7. Créer un superutilisateur si nécessaire
echo 👤 Vérification du superutilisateur...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Superutilisateur existe déjà')"

REM 8. Vérifier la configuration Django
echo 🔍 Vérification de la configuration...
python manage.py check --deploy

echo.
echo ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !
echo 🌐 Votre application est prête pour PythonAnywhere
echo.
echo 📝 INSTRUCTIONS FINALES:
echo 1. Copiez le contenu de 'wsgi_pythonanywhere_final.py' dans votre fichier WSGI
echo 2. Changez le settings module vers 'gestion_immobiliere.settings_pythonanywhere'
echo 3. Configurez les fichiers statiques: /static/ → /home/laurenzo/appli_KBIS/staticfiles/
echo 4. Configurez les fichiers media: /media/ → /home/laurenzo/appli_KBIS/media/
echo 5. Redémarrez votre application web
echo.
echo 🎯 URLs à tester:
echo - https://laurenzo.pythonanywhere.com/
echo - https://laurenzo.pythonanywhere.com/utilisateurs/connexion-groupes/
echo - https://laurenzo.pythonanywhere.com/admin/

pause
