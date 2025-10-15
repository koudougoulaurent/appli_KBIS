Write-Host "=== DEMARRAGE GESTIMMOB ===" -ForegroundColor Green
Write-Host "Demarrage du serveur Django..." -ForegroundColor Cyan

$env:DJANGO_SETTINGS_MODULE="gestion_immobiliere.settings"
python manage.py runserver --noreload
