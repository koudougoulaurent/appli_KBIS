# Script de démarrage automatique pour GESTIMMOB
# Usage: .\start_server.ps1

Write-Host "🚀 Démarrage du serveur GESTIMMOB..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Blue

# Arrêter les processus Python existants
Write-Host "🛑 Arrêt des processus Python existants..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Aller à la racine du projet
$projectRoot = "C:\Users\GAMER\Desktop\gestionImo"
Write-Host "📁 Navigation vers: $projectRoot" -ForegroundColor Cyan
Set-Location $projectRoot

# Vérifier que l'environnement virtuel existe
if (-Not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Environnement virtuel non trouvé!" -ForegroundColor Red
    Write-Host "Créez l'environnement virtuel avec: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activer l'environnement virtuel
Write-Host "🐍 Activation de l'environnement virtuel..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Aller dans le dossier Django
Write-Host "📂 Navigation vers appli_KBIS..." -ForegroundColor Cyan
Set-Location "appli_KBIS"

# Vérifier que manage.py existe
if (-Not (Test-Path "manage.py")) {
    Write-Host "❌ Fichier manage.py non trouvé!" -ForegroundColor Red
    Write-Host "Vérifiez que vous êtes dans le bon dossier." -ForegroundColor Yellow
    exit 1
}

# Vérifier la configuration Django
Write-Host "🔍 Vérification de la configuration Django..." -ForegroundColor Yellow
$checkResult = & python manage.py check 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreurs de configuration Django détectées:" -ForegroundColor Red
    Write-Host $checkResult -ForegroundColor Red
    Write-Host "Corrigez les erreurs avant de continuer." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Configuration Django OK" -ForegroundColor Green

# Appliquer les migrations
Write-Host "📦 Application des migrations..." -ForegroundColor Yellow
$migrateResult = & python manage.py migrate 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors des migrations:" -ForegroundColor Red
    Write-Host $migrateResult -ForegroundColor Red
    exit 1
}
Write-Host "✅ Migrations appliquées" -ForegroundColor Green

# Collecter les fichiers statiques
Write-Host "📁 Collection des fichiers statiques..." -ForegroundColor Yellow
$staticResult = & python manage.py collectstatic --noinput 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Avertissement lors de la collection des fichiers statiques:" -ForegroundColor Yellow
    Write-Host $staticResult -ForegroundColor Yellow
} else {
    Write-Host "✅ Fichiers statiques collectés" -ForegroundColor Green
}

# Vérifier que le port 8000 est libre
Write-Host "🔌 Vérification du port 8000..." -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "⚠️ Le port 8000 est déjà utilisé. Utilisation du port 8001..." -ForegroundColor Yellow
    $port = "8001"
} else {
    $port = "8000"
}

# Afficher les informations de démarrage
Write-Host "=" * 50 -ForegroundColor Blue
Write-Host "🌐 Démarrage du serveur Django..." -ForegroundColor Green
Write-Host "📍 URL: http://127.0.0.1:$port/" -ForegroundColor Cyan
Write-Host "🛑 Pour arrêter le serveur: Ctrl+C" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Blue

# Démarrer le serveur Django
try {
    & python manage.py runserver "127.0.0.1:$port" --verbosity=2
} catch {
    Write-Host "❌ Erreur lors du démarrage du serveur:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "👋 Serveur arrêté." -ForegroundColor Yellow
