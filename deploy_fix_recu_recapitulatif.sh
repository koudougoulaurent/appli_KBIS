#!/bin/bash

# Script de déploiement pour corriger le problème RecuRecapitulatif
# Usage: ./deploy_fix_recu_recapitulatif.sh

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

echo "2. Vérification de la syntaxe Python..."
cd "$PROJECT_PATH"
python -m py_compile paiements/views_recus.py

echo "3. Vérification Django..."
python manage.py check

echo "4. Redémarrage des services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "5. Vérification du statut des services..."
sudo systemctl status gunicorn --no-pager -l
sudo systemctl status nginx --no-pager -l

echo "=== Déploiement terminé avec succès ==="
echo "Sauvegarde créée: $BACKUP_DIR/views_recus.py.backup_$TIMESTAMP"
