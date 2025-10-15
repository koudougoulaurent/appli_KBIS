Write-Host "Demarrage du serveur Django..." -ForegroundColor Green
Remove-Item Env:DJANGO_SETTINGS_MODULE -ErrorAction SilentlyContinue
$env:PYTHONPATH = "01_DJANGO_APPS;$env:PYTHONPATH"
$env:DJANGO_SETTINGS_MODULE = "gestion_immobiliere.settings"
python manage.py runserver --noreload
