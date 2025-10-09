# =====================================================
# SCRIPT DE DÉPLOIEMENT - SYSTÈME AVANCES INTELLIGENTES
# =====================================================
# Date: 09/10/2025
# Version: 2.0
# Description: Déploiement automatisé des avances intelligentes (Windows)
# =====================================================

param(
    [string]$ProjectDir = "C:\Users\GAMER\Documents\appli_KBIS",
    [string]$BackupDir = "C:\backups\appli_KBIS",
    [string]$LogFile = "C:\logs\appli_KBIS\deploy.log"
)

# Fonction pour afficher les messages
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        default { Write-Host $logMessage -ForegroundColor Blue }
    }
    
    # Écrire dans le fichier de log
    $logDir = Split-Path $LogFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $LogFile -Value $logMessage
}

# Fonction de sauvegarde
function Backup-Database {
    Write-Log "Création de la sauvegarde de la base de données..."
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    if (!(Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    
    # Sauvegarder la base de données
    Set-Location $ProjectDir
    $backupFile = "$BackupDir\backup_avant_avances_intelligentes_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    try {
        python manage.py dumpdata | Out-File -FilePath $backupFile -Encoding UTF8
        Write-Log "Sauvegarde créée avec succès: $backupFile" "SUCCESS"
    }
    catch {
        Write-Log "Échec de la sauvegarde: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction de mise à jour du code
function Update-Code {
    Write-Log "Mise à jour du code source..."
    
    Set-Location $ProjectDir
    
    try {
        # Sauvegarder les modifications locales
        git stash push -m "Sauvegarde avant déploiement avances intelligentes $(Get-Date -Format 'yyyyMMdd_HHmmss')"
        
        # Récupérer les dernières modifications
        git fetch origin
        git checkout modifications-octobre-2025
        git pull origin modifications-octobre-2025
        
        Write-Log "Code mis à jour avec succès" "SUCCESS"
    }
    catch {
        Write-Log "Échec de la mise à jour du code: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction d'installation des dépendances
function Install-Dependencies {
    Write-Log "Installation des dépendances..."
    
    Set-Location $ProjectDir
    
    # Activer l'environnement virtuel s'il existe
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
        Write-Log "Environnement virtuel activé"
    }
    
    try {
        # Installer les dépendances
        pip install -r requirements.txt
        Write-Log "Dépendances installées avec succès" "SUCCESS"
    }
    catch {
        Write-Log "Échec de l'installation des dépendances: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction d'application des migrations
function Apply-Migrations {
    Write-Log "Application des migrations..."
    
    Set-Location $ProjectDir
    
    try {
        # Vérifier l'état des migrations
        Write-Log "État des migrations avant application:"
        python manage.py showmigrations paiements
        
        # Appliquer les migrations dans l'ordre
        Write-Log "Application de la migration 0011..."
        python manage.py migrate paiements 0011
        
        Write-Log "Application de la migration 0012..."
        python manage.py migrate paiements 0012
        
        # Vérifier l'état des migrations après application
        Write-Log "État des migrations après application:"
        python manage.py showmigrations paiements
        
        Write-Log "Migrations appliquées avec succès" "SUCCESS"
    }
    catch {
        Write-Log "Échec de l'application des migrations: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction de correction des données
function Fix-Data {
    Write-Log "Correction des données existantes..."
    
    Set-Location $ProjectDir
    
    try {
        # Script de correction des données
        $correctionScript = @"
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

print("Début de la correction des données...")

# Corriger les avances avec des dates incorrectes
avances_corrigees = 0
for avance in AvanceLoyer.objects.all():
    corrected = False
    if avance.mois_debut_couverture and avance.mois_debut_couverture.year < 2000:
        avance.mois_debut_couverture = avance.mois_debut_couverture.replace(year=avance.mois_debut_couverture.year + 2000)
        corrected = True
    if avance.mois_fin_couverture and avance.mois_fin_couverture.year < 2000:
        avance.mois_fin_couverture = avance.mois_fin_couverture.replace(year=avance.mois_fin_couverture.year + 2000)
        corrected = True
    if corrected:
        avance.save()
        avances_corrigees += 1

print(f"Avances corrigées: {avances_corrigees}")

# Supprimer les consommations avec des dates incorrectes
consommations_supprimees = ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).count()
ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).delete()

print(f"Consommations supprimées: {consommations_supprimees}")

# Recalculer les montants restants
for avance in AvanceLoyer.objects.all():
    avance.montant_restant = avance.montant_avance
    avance.statut = 'active'
    avance.save()

print("Correction des données terminée")
"@
        
        $correctionScript | python manage.py shell
        Write-Log "Données corrigées avec succès" "SUCCESS"
    }
    catch {
        Write-Log "Échec de la correction des données: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction de vérification
function Verify-Deployment {
    Write-Log "Vérification du déploiement..."
    
    Set-Location $ProjectDir
    
    try {
        # Vérifier l'intégrité des données
        $verificationScript = @"
from paiements.models_avance import AvanceLoyer

print("Vérification de l'intégrité des données...")

# Vérifier les avances
avances = AvanceLoyer.objects.all()
print(f"Total avances: {avances.count()}")

# Vérifier les avances avec des problèmes
problemes = avances.filter(montant_restant__lt=0)
print(f"Avances avec montant restant négatif: {problemes.count()}")

# Vérifier les dates
dates_incorrectes = avances.filter(mois_debut_couverture__year__lt=2000)
print(f"Avances avec dates incorrectes: {dates_incorrectes.count()}")

# Vérifier les nouveaux champs
champs_manquants = avances.filter(paiement__isnull=True).count()
print(f"Avances sans paiement associé: {champs_manquants}")

print("Vérification terminée")
"@
        
        $verificationScript | python manage.py shell
        Write-Log "Vérification réussie" "SUCCESS"
    }
    catch {
        Write-Log "Échec de la vérification: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction de test
function Test-Functionality {
    Write-Log "Test des nouvelles fonctionnalités..."
    
    Set-Location $ProjectDir
    
    try {
        # Test de création d'avance
        $testScript = @"
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from decimal import Decimal
from datetime import date

print("Test de création d'avance...")

# Récupérer un contrat
contrat = Contrat.objects.first()
if contrat:
    try:
        # Créer une avance de test
        avance = ServiceGestionAvance.creer_avance_loyer(
            contrat=contrat,
            montant_avance=Decimal('100000'),
            date_avance=date.today(),
            notes="Test déploiement"
        )
        print(f"Avance créée: {avance.id}, Statut: {avance.statut}")
        print(f"Paiement associé: {avance.paiement}")
        
        # Supprimer l'avance de test
        avance.delete()
        print("Test terminé avec succès")
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        raise
else:
    print("Aucun contrat trouvé pour le test")
    raise Exception("Aucun contrat disponible pour le test")
"@
        
        $testScript | python manage.py shell
        Write-Log "Test des fonctionnalités réussi" "SUCCESS"
    }
    catch {
        Write-Log "Échec du test des fonctionnalités: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Fonction principale
function Main {
    Write-Log "=== DÉBUT DU DÉPLOIEMENT DES AVANCES INTELLIGENTES ==="
    
    # Vérifier que nous sommes dans le bon répertoire
    if (!(Test-Path "$ProjectDir\manage.py")) {
        Write-Log "Répertoire de projet incorrect: $ProjectDir" "ERROR"
        exit 1
    }
    
    # Exécuter les étapes de déploiement
    Backup-Database
    Update-Code
    Install-Dependencies
    Apply-Migrations
    Fix-Data
    Verify-Deployment
    Test-Functionality
    
    Write-Log "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ===" "SUCCESS"
    
    # Afficher les informations de post-déploiement
    Write-Host ""
    Write-Host "🎉 DÉPLOIEMENT RÉUSSI !" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Informations importantes:" -ForegroundColor Cyan
    Write-Host "   - Sauvegarde: $BackupDir" -ForegroundColor White
    Write-Host "   - Logs: $LogFile" -ForegroundColor White
    Write-Host "   - Projet: $ProjectDir" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Prochaines étapes:" -ForegroundColor Cyan
    Write-Host "   1. Vérifier l'application dans le navigateur" -ForegroundColor White
    Write-Host "   2. Tester la création d'avances" -ForegroundColor White
    Write-Host "   3. Surveiller les logs pour détecter d'éventuels problèmes" -ForegroundColor White
    Write-Host ""
    Write-Host "📞 En cas de problème:" -ForegroundColor Cyan
    Write-Host "   - Consulter les logs: Get-Content $LogFile -Tail 50" -ForegroundColor White
    Write-Host "   - Restaurer la sauvegarde si nécessaire" -ForegroundColor White
    Write-Host ""
}

# Exécuter le script principal
Main
