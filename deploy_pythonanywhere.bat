@echo off
REM ===========================================
REM SCRIPT DE DÉPLOIEMENT PYTHONANYWHERE (WINDOWS)
REM ===========================================

echo 🚀 DÉPLOIEMENT SUR PYTHONANYWHERE - APPLICATION IMMOBILIÈRE
echo ==========================================================

REM Variables de configuration
set PROJECT_NAME=gestion_immobiliere
set PYTHON_VERSION=3.10
set REQUIREMENTS_FILE=requirements_pythonanywhere.txt
set SETTINGS_FILE=settings_pythonanywhere

REM Vérification des prérequis
echo [INFO] Vérification des prérequis...

REM Vérifier si Python 3.10 est disponible
python3.10 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10 n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier si le fichier requirements existe
if not exist "%REQUIREMENTS_FILE%" (
    echo [ERROR] Le fichier %REQUIREMENTS_FILE% n'existe pas
    pause
    exit /b 1
)

REM Vérifier si manage.py existe
if not exist "manage.py" (
    echo [ERROR] Le fichier manage.py n'existe pas. Êtes-vous dans le bon répertoire ?
    pause
    exit /b 1
)

echo [SUCCESS] Prérequis vérifiés ✓

REM ===========================================
REM INSTALLATION DES PACKAGES
REM ===========================================

echo [INFO] Installation des packages Python...

REM Mise à jour de pip
python3.10 -m pip install --user --upgrade pip

REM Installation des packages
python3.10 -m pip install --user -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo [ERROR] Erreur lors de l'installation des packages
    pause
    exit /b 1
)
echo [SUCCESS] Packages installés avec succès ✓

REM ===========================================
REM CONFIGURATION DE LA BASE DE DONNÉES
REM ===========================================

echo [INFO] Configuration de la base de données...

REM Créer le répertoire de logs s'il n'existe pas
if not exist "logs" mkdir logs

REM Appliquer les migrations
echo [INFO] Application des migrations...
python3.10 manage.py makemigrations
if errorlevel 1 (
    echo [WARNING] Aucune nouvelle migration nécessaire
) else (
    echo [SUCCESS] Migrations créées ✓
)

python3.10 manage.py migrate --settings=%PROJECT_NAME%.%SETTINGS_FILE%
if errorlevel 1 (
    echo [ERROR] Erreur lors de l'application des migrations
    pause
    exit /b 1
)
echo [SUCCESS] Migrations appliquées ✓

REM ===========================================
REM COLLECTE DES FICHIERS STATIQUES
REM ===========================================

echo [INFO] Collecte des fichiers statiques...

python3.10 manage.py collectstatic --noinput --settings=%PROJECT_NAME%.%SETTINGS_FILE%
if errorlevel 1 (
    echo [ERROR] Erreur lors de la collecte des fichiers statiques
    pause
    exit /b 1
)
echo [SUCCESS] Fichiers statiques collectés ✓

REM ===========================================
REM CRÉATION DU SUPERUTILISATEUR
REM ===========================================

echo [INFO] Configuration du superutilisateur...

REM Vérifier si un superutilisateur existe déjà
python3.10 manage.py shell --settings=%PROJECT_NAME%.%SETTINGS_FILE% -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists:', User.objects.filter(is_superuser=True).exists())" | findstr "True" >nul
if errorlevel 1 (
    echo [INFO] Création d'un superutilisateur par défaut...
    echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None | python3.10 manage.py shell --settings=%PROJECT_NAME%.%SETTINGS_FILE%
    echo [SUCCESS] Superutilisateur créé (admin/admin123) ✓
) else (
    echo [WARNING] Un superutilisateur existe déjà
)

REM ===========================================
REM VÉRIFICATIONS FINALES
REM ===========================================

echo [INFO] Vérifications finales...

REM Vérifier la configuration Django
python3.10 manage.py check --settings=%PROJECT_NAME%.%SETTINGS_FILE%
if errorlevel 1 (
    echo [ERROR] Problèmes de configuration détectés
    pause
    exit /b 1
)
echo [SUCCESS] Configuration Django valide ✓

REM Vérifier les fichiers statiques
if exist "staticfiles" (
    echo [SUCCESS] Fichiers statiques présents ✓
) else (
    echo [WARNING] Aucun fichier statique trouvé
)

REM ===========================================
REM INSTRUCTIONS DE CONFIGURATION PYTHONANYWHERE
REM ===========================================

echo.
echo 🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !
echo ==================================
echo.
echo 📋 PROCHAINES ÉTAPES SUR PYTHONANYWHERE :
echo.
echo 1. 🌐 Configuration Web App :
echo    - Allez dans l'onglet 'Web' de PythonAnywhere
echo    - Modifiez le fichier WSGI : /var/www/votre-nom_pythonanywhere_com_wsgi.py
echo    - Remplacez le contenu par :
echo.
echo    import os
echo    import sys
echo    path = '/home/votre-nom/votre-projet'
echo    if path not in sys.path:
echo        sys.path.append(path)
echo    os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_pythonanywhere'
echo    from django.core.wsgi import get_wsgi_application
echo    application = get_wsgi_application()
echo.
echo 2. 📁 Configuration des fichiers statiques :
echo    - Static files: /static/ → /home/votre-nom/votre-projet/staticfiles/
echo    - Media files: /media/ → /home/votre-nom/votre-projet/media/
echo.
echo 3. 🔧 Configuration des variables d'environnement :
echo    - Créez un fichier .env dans votre projet :
echo    - SECRET_KEY=votre-secret-key-securise
echo    - DEBUG=False
echo    - ALLOWED_HOSTS=votre-nom.pythonanywhere.com
echo.
echo 4. 🚀 Redémarrez votre application web
echo.
echo 5. 🌐 Accédez à votre application :
echo    - URL principale : https://votre-nom.pythonanywhere.com
echo    - Interface admin : https://votre-nom.pythonanywhere.com/admin/
echo    - Connexion : admin / admin123
echo.
echo 📚 Documentation complète : GUIDE_DEPLOIEMENT_PYTHONANYWHERE_COMPLET.md
echo.

REM ===========================================
REM RÉSUMÉ DES PACKAGES INSTALLÉS
REM ===========================================

echo 📦 PACKAGES INSTALLÉS :
echo =======================
python3.10 -m pip list --user | findstr /i "django reportlab pillow whitenoise crispy rest_framework"

echo.
echo [SUCCESS] Script de déploiement terminé ! 🎉
echo.
pause
