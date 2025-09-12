@echo off
echo ========================================
echo    DEPLOIEMENT FACILE SUR LWS
echo ========================================
echo.

echo [1/4] Preparation du projet...
echo.

REM Creer le dossier de deploiement
if not exist "deploiement_lws" mkdir "deploiement_lws"
cd deploiement_lws

echo [2/4] Copie des fichiers essentiels...
echo.

REM Copier tous les fichiers du projet
xcopy "..\*" "." /E /I /Y /EXCLUDE:exclude.txt >nul 2>&1

REM Creer le fichier exclude.txt pour ignorer certains fichiers
echo db.sqlite3 > exclude.txt
echo *.log >> exclude.txt
echo __pycache__ >> exclude.txt
echo .git >> exclude.txt
echo logs >> exclude.txt
echo media >> exclude.txt

echo [3/4] Configuration pour LWS...
echo.

REM Modifier le fichier wsgi.py pour LWS
echo import os > wsgi_lws.py
echo import sys >> wsgi_lws.py
echo. >> wsgi_lws.py
echo path = '/www/appli_KBIS' >> wsgi_lws.py
echo if path not in sys.path: >> wsgi_lws.py
echo     sys.path.append(path) >> wsgi_lws.py
echo. >> wsgi_lws.py
echo os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_lws') >> wsgi_lws.py
echo. >> wsgi_lws.py
echo from django.core.wsgi import get_wsgi_application >> wsgi_lws.py
echo application = get_wsgi_application() >> wsgi_lws.py

REM Renommer le fichier wsgi.py original
if exist "wsgi.py" ren "wsgi.py" "wsgi_original.py"
ren "wsgi_lws.py" "wsgi.py"

echo [4/4] Creation du script de deploiement LWS...
echo.

REM Creer le script de deploiement pour LWS
echo #!/bin/bash > deploy_lws.bat
echo echo Deploiement sur LWS... >> deploy_lws.bat
echo pip install -r requirements_production.txt --user >> deploy_lws.bat
echo python manage.py makemigrations >> deploy_lws.bat
echo python manage.py migrate >> deploy_lws.bat
echo python manage.py collectstatic --noinput >> deploy_lws.bat
echo python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" >> deploy_lws.bat
echo echo Deploiement termine! >> deploy_lws.bat

echo.
echo ========================================
echo    PREPARATION TERMINEE !
echo ========================================
echo.
echo PROCHAINES ETAPES:
echo.
echo 1. Allez sur lws.fr et creez votre compte
echo 2. Choisissez le plan "Python" (3-5€/mois)
echo 3. Dans l'espace LWS, allez dans "Fichiers"
echo 4. Uploadez TOUT le contenu du dossier "deploiement_lws"
echo 5. Dans le terminal LWS, executez: bash deploy_lws.bat
echo 6. Votre site sera accessible sur votre-nom.lws.fr
echo.
echo CONNEXION ADMIN:
echo - Utilisateur: admin
echo - Mot de passe: admin123
echo - URL: https://votre-nom.lws.fr/admin/
echo.
echo ========================================
echo.
pause





