@echo off
echo ========================================
echo    RESTAURATION ETAT 2 - Gestion Immobiliere
echo ========================================
echo.

echo [1/5] Arret du serveur Django...
taskkill /f /im python.exe 2>nul
echo.

echo [2/5] Copie des fichiers de sauvegarde...
robocopy "%~dp0" "..\..\" /E /XD backups /NFL /NDL /NJH /NJS /NC /NS
if %errorlevel% geq 8 (
    echo ERREUR: Echec de la copie des fichiers
    pause
    exit /b 1
)
echo.

echo [3/5] Installation des dependances...
cd "..\.."
pip install -r requirements.txt
echo.

echo [4/5] Application des migrations...
python manage.py migrate
echo.

echo [5/5] Demarrage du serveur...
echo.
echo ========================================
echo    RESTAURATION TERMINEE AVEC SUCCES !
echo ========================================
echo.
echo L'application est maintenant disponible sur :
echo - Dashboard : http://127.0.0.1:8000/
echo - Interface API : http://127.0.0.1:8000/api-interface/
echo - Administration : http://127.0.0.1:8000/admin/
echo.
echo Appuyez sur une touche pour demarrer le serveur...
pause

python manage.py runserver 