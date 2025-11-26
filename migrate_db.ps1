# Script PowerShell pour exécuter les migrations avec le bon settings
$env:DJANGO_SETTINGS_MODULE = 'gestion_immobiliere.settings_postgresql'
python manage.py migrate


