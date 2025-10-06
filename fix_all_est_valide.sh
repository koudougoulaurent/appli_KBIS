#!/bin/bash

# Script pour corriger toutes les références à est_valide

echo "🔧 Correction de toutes les références à est_valide..."

# Répertoire de l'application
cd /var/www/kbis_immobilier

# Rechercher et remplacer est_valide par statut dans tous les fichiers Python
find . -name "*.py" -type f -not -path "./venv/*" -not -path "./.git/*" | while read file; do
    if grep -q "est_valide" "$file"; then
        echo "Correction de $file..."
        
        # Créer une sauvegarde
        cp "$file" "$file.backup_$(date +%Y%m%d_%H%M%S)"
        
        # Remplacer toutes les occurrences de est_valide par statut
        sed -i 's/est_valide__/statut__/g' "$file"
        sed -i 's/est_valide=/statut=/g' "$file"
        sed -i 's/est_valide,/statut,/g' "$file"
        sed -i 's/est_valide)/statut)/g' "$file"
        sed -i 's/est_valide"/statut"/g' "$file"
        sed -i "s/est_valide'/statut'/g" "$file"
        sed -i 's/\.est_valide/.statut/g' "$file"
        sed -i 's/\["est_valide"\]/["statut"]/g' "$file"
        sed -i "s/\['est_valide'\]/['statut']/g" "$file"
        sed -i 's/"est_valide"/"statut"/g' "$file"
        sed -i "s/'est_valide'/'statut'/g" "$file"
        
        echo "  ✅ $file corrigé"
    fi
done

echo "✅ Toutes les références à est_valide ont été corrigées"
echo ""
echo "🔄 Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

echo "✅ Correction terminée !"

