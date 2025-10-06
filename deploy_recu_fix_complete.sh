#!/bin/bash

# Script de déploiement complet pour corriger le problème RecuRecapitulatif
# Usage: ./deploy_recu_fix_complete.sh

set -e  # Arrêter en cas d'erreur

echo "=== Déploiement de la correction RecuRecapitulatif ==="
echo "Date: $(date)"

# Variables
PROJECT_PATH="/var/www/kbis_immobilier"
BACKUP_DIR="/var/www/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p "$BACKUP_DIR"

echo "1. Sauvegarde du fichier actuel..."
cp "$PROJECT_PATH/paiements/views_recus.py" "$BACKUP_DIR/views_recus.py.backup_$TIMESTAMP"

echo "2. Application de la correction..."
cd "$PROJECT_PATH"

# Appliquer la correction en utilisant sed pour modifier le fichier directement
echo "Modification de la fonction liste_recus_recapitulatifs..."

# Ajouter l'import local au début de la fonction liste_recus_recapitulatifs
sed -i '/def liste_recus_recapitulatifs(request):/,/Vérification des permissions/ {
    /Vérification des permissions/ {
        i\
    # Import local pour éviter les problèmes d'\''import en production\
    try:\
        from .models import RecuRecapitulatif\
    except ImportError:\
        # Fallback si l'\''import échoue\
        RecuRecapitulatif = None\
    \
    # Vérification des permissions
    }
}' paiements/views_recus.py

echo "Modification de la fonction creer_recu_recapitulatif..."

# Ajouter l'import local au début de la fonction creer_recu_recapitulatif
sed -i '/def creer_recu_recapitulatif(request, recapitulatif_id):/,/Vérification des permissions/ {
    /Vérification des permissions/ {
        i\
    # Import local pour éviter les problèmes d'\''import en production\
    try:\
        from .models import RecuRecapitulatif\
    except ImportError:\
        # Fallback si l'\''import échoue\
        RecuRecapitulatif = None\
    \
    # Vérification des permissions
    }
}' paiements/views_recus.py

echo "3. Vérification de la syntaxe Python..."
python -m py_compile paiements/views_recus.py

echo "4. Vérification Django..."
python manage.py check

echo "5. Redémarrage des services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "6. Vérification du statut des services..."
sudo systemctl status gunicorn --no-pager -l
sudo systemctl status nginx --no-pager -l

echo "=== Déploiement terminé avec succès ==="
echo "Sauvegarde créée: $BACKUP_DIR/views_recus.py.backup_$TIMESTAMP"
echo "Vous pouvez maintenant tester l'URL: https://78.138.58.185/paiements/recus-recapitulatifs/creer/1/"
