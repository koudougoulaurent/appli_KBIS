#!/bin/bash

# Script DIRECT pour corriger les imports manquants
echo "Correction DIRECTE des imports manquants..."

cd /var/www/kbis_immobilier

# 1. Verifier le fichier views_recus.py
echo "1. Verification du fichier views_recus.py..."

if [ -f "paiements/views_recus.py" ]; then
    echo "Contenu actuel des imports dans views_recus.py:"
    head -20 "paiements/views_recus.py" | grep -E "(import|from)"
    echo ""
    
    # Creer une sauvegarde
    cp "paiements/views_recus.py" "paiements/views_recus.py.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Ajouter les imports manquants DIRECTEMENT
    echo "Ajout des imports manquants..."
    
    # Ajouter les imports au debut du fichier
    sed -i '1i from .models import RecapMensuel, RecuRecapitulatif' "paiements/views_recus.py"
    
    echo "  OK: Imports ajoutes"
    
    echo ""
    echo "Contenu des imports apres correction:"
    head -20 "paiements/views_recus.py" | grep -E "(import|from)"
    echo ""
    
else
    echo "ATTENTION: fichier views_recus.py introuvable"
fi

# 2. Verifier les autres fichiers
echo "2. Verification des autres fichiers..."

files=(
    "paiements/views_charges_avancees.py"
    "paiements/views_kbis_recus.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Verification de $file..."
        
        # Creer une sauvegarde
        cp "$file" "$file.backup_$(date +%Y%m%d_%H%M%S)"
        
        # Ajouter l'import RecapMensuel
        sed -i '1i from .models import RecapMensuel' "$file"
        
        echo "  OK: Import RecapMensuel ajoute dans $file"
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

# 3. Tester Django
echo "3. Test de Django..."

# Tester que Django peut se charger
python manage.py check

if [ $? -eq 0 ]; then
    echo "OK: Django peut se charger sans erreur"
else
    echo "ATTENTION: Django a des erreurs"
fi

# 4. Redemarrer Gunicorn
echo "4. Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction DIRECTE des imports terminee!"
echo "Les imports RecapMensuel et RecuRecapitulatif ont ete ajoutes DIRECTEMENT"
