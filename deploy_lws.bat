@echo off
echo ========================================
echo    DEPLOIEMENT AUTOMATIQUE LWS
echo ========================================
echo.

echo [1/5] Installation des dependances...
pip install -r requirements_production.txt --user
if errorlevel 1 (
    echo ERREUR: Impossible d'installer les dependances
    pause
    exit /b 1
)

echo.
echo [2/5] Creation des migrations...
python manage.py makemigrations
if errorlevel 1 (
    echo ERREUR: Probleme avec les migrations
    pause
    exit /b 1
)

echo.
echo [3/5] Application des migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERREUR: Probleme avec la base de donnees
    pause
    exit /b 1
)

echo.
echo [4/5] Collecte des fichiers statiques...
python manage.py collectstatic --noinput
if errorlevel 1 (
    echo ERREUR: Probleme avec les fichiers statiques
    pause
    exit /b 1
)

echo.
echo [5/5] Creation du superutilisateur...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Superutilisateur existe deja')"

echo.
echo ========================================
echo    DEPLOIEMENT TERMINE !
echo ========================================
echo.
echo Votre application Django est maintenant en ligne !
echo.
echo INFORMATIONS DE CONNEXION:
echo - URL: https://votre-nom.lws.fr
echo - Admin: https://votre-nom.lws.fr/admin/
echo - Utilisateur: admin
echo - Mot de passe: admin123
echo.
echo IMPORTANT: Changez le mot de passe admin !
echo.
echo ========================================
pause





