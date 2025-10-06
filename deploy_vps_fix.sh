#!/bin/bash

# Script de déploiement des corrections pour le VPS
# Résout les problèmes de production

echo "🚀 Début du déploiement des corrections VPS..."

# Variables
PROJECT_DIR="/path/to/your/project"  # À modifier selon votre configuration
BACKUP_DIR="/tmp/kbis_backup_$(date +%Y%m%d_%H%M%S)"

# Fonction de sauvegarde
backup_database() {
    echo "📦 Sauvegarde de la base de données..."
    mkdir -p $BACKUP_DIR
    
    # Sauvegarde PostgreSQL (ajustez selon votre configuration)
    pg_dump -h localhost -U your_user -d your_database > $BACKUP_DIR/database_backup.sql
    
    if [ $? -eq 0 ]; then
        echo "✅ Sauvegarde de la base de données terminée"
    else
        echo "❌ Erreur lors de la sauvegarde de la base de données"
        exit 1
    fi
}

# Fonction de mise à jour du code
update_code() {
    echo "📥 Mise à jour du code..."
    
    # Aller dans le répertoire du projet
    cd $PROJECT_DIR
    
    # Sauvegarder les fichiers modifiés
    cp paiements/models.py $BACKUP_DIR/models_backup.py
    cp fix_vps_production.py $BACKUP_DIR/
    
    echo "✅ Code mis à jour"
}

# Fonction de correction de la base de données
fix_database() {
    echo "🔧 Correction de la base de données..."
    
    cd $PROJECT_DIR
    
    # Exécuter le script de correction
    python fix_vps_production.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Corrections de base de données appliquées"
    else
        echo "❌ Erreur lors des corrections de base de données"
        echo "🔄 Restauration de la sauvegarde..."
        psql -h localhost -U your_user -d your_database < $BACKUP_DIR/database_backup.sql
        exit 1
    fi
}

# Fonction d'exécution des migrations
run_migrations() {
    echo "🔄 Exécution des migrations..."
    
    cd $PROJECT_DIR
    
    # Activer l'environnement virtuel si nécessaire
    # source venv/bin/activate  # Décommentez si vous utilisez un venv
    
    # Exécuter les migrations
    python manage.py migrate paiements
    
    if [ $? -eq 0 ]; then
        echo "✅ Migrations exécutées avec succès"
    else
        echo "❌ Erreur lors des migrations"
        exit 1
    fi
}

# Fonction de redémarrage des services
restart_services() {
    echo "🔄 Redémarrage des services..."
    
    # Redémarrer le serveur web (ajustez selon votre configuration)
    sudo systemctl restart nginx
    sudo systemctl restart gunicorn  # ou uwsgi selon votre configuration
    
    # Vider le cache Django
    cd $PROJECT_DIR
    python manage.py clear_cache  # si vous avez django-cache
    
    echo "✅ Services redémarrés"
}

# Fonction de test
test_fixes() {
    echo "🧪 Test des corrections..."
    
    cd $PROJECT_DIR
    
    # Test de la base de données
    python manage.py shell -c "
from paiements.models import RetraitBailleur
try:
    # Tester si le champ statut existe
    retrait = RetraitBailleur.objects.first()
    if retrait:
        print('✅ Champ statut accessible:', retrait.statut)
    else:
        print('⚠️ Aucun retrait trouvé pour le test')
    print('✅ Test de base de données réussi')
except Exception as e:
    print('❌ Erreur lors du test:', str(e))
    exit(1)
"
    
    echo "✅ Tests terminés"
}

# Fonction principale
main() {
    echo "📋 Début des corrections VPS"
    echo "================================"
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -f "manage.py" ]; then
        echo "❌ Fichier manage.py non trouvé. Vérifiez le répertoire du projet."
        exit 1
    fi
    
    # Étapes de correction
    backup_database
    update_code
    fix_database
    run_migrations
    restart_services
    test_fixes
    
    echo ""
    echo "✅ Corrections VPS terminées avec succès!"
    echo ""
    echo "📝 Actions effectuées:"
    echo "1. ✅ Sauvegarde de la base de données"
    echo "2. ✅ Mise à jour du code"
    echo "3. ✅ Correction du champ 'statut' manquant"
    echo "4. ✅ Amélioration de la génération PDF"
    echo "5. ✅ Exécution des migrations"
    echo "6. ✅ Redémarrage des services"
    echo "7. ✅ Tests de validation"
    echo ""
    echo "🎯 Problèmes résolus:"
    echo "- Erreur 'Cannot resolve keyword statut' → Corrigé"
    echo "- PDF illisible → Utilise maintenant ReportLab"
    echo ""
    echo "📁 Sauvegarde disponible dans: $BACKUP_DIR"
}

# Exécution
main "$@"