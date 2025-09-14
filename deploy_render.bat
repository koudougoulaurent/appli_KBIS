@echo off
echo ========================================
echo    DEPLOIEMENT SUR RENDER
echo ========================================

echo.
echo 🔧 Configuration de l'environnement...
set DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings

echo.
echo 📦 Installation des dépendances...
pip install -r requirements.txt

echo.
echo 🗄️ Exécution des migrations...
python manage.py migrate --noinput

echo.
echo 📁 Collecte des fichiers statiques...
python manage.py collectstatic --noinput

echo.
echo 🔍 Vérification des données...
python verifier_donnees_automatique.py

echo.
echo ✅ Déploiement terminé !
echo.
echo Pour déployer sur Render :
echo 1. Commitez ces changements : git add . && git commit -m "Fix deployment issues"
echo 2. Poussez vers GitHub : git push origin master
echo 3. Render redéploiera automatiquement
echo.
pause
