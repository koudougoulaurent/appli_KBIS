# Script pour supprimer la variable d'environnement DJANGO_SETTINGS_MODULE problématique
# Exécutez ce script une fois pour supprimer la variable de votre session PowerShell

if ($env:DJANGO_SETTINGS_MODULE -eq 'packages.hotspot.settings_dev') {
    Remove-Item Env:DJANGO_SETTINGS_MODULE
    Write-Host "Variable DJANGO_SETTINGS_MODULE supprimée avec succès!" -ForegroundColor Green
    Write-Host "Vous pouvez maintenant utiliser 'python manage.py migrate' normalement." -ForegroundColor Green
} else {
    Write-Host "La variable DJANGO_SETTINGS_MODULE n'est pas définie ou a une autre valeur." -ForegroundColor Yellow
    Write-Host "Valeur actuelle: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Yellow
}


