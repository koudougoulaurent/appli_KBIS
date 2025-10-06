#!/bin/bash

# Script pour corriger les references sur le VPS
echo "Correction des references RecapitulatifMensuelBailleur sur le VPS..."

cd /var/www/kbis_immobilier

# Fichiers a corriger
files=(
    "paiements/views_recus.py"
    "paiements/views_kbis_recus.py"
    "paiements/forms.py"
    "paiements/services_recus.py"
    "paiements/views_charges_avancees.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Correction de $file..."
        
        # Creer une sauvegarde
        cp "$file" "$file.backup"
        
        # Remplacer toutes les occurrences
        sed -i 's/RecapitulatifMensuelBailleur/RecapMensuel/g' "$file"
        
        echo "  OK: $file corrige"
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

echo "Correction terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

echo "Correction terminee avec succes!"
