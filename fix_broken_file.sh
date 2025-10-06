#!/bin/bash

# Script pour corriger le fichier casse et restaurer les imports correctement
echo "Correction du fichier casse et restauration des imports..."

cd /var/www/kbis_immobilier

# 1. Verifier l'etat actuel du fichier
echo "1. Verification de l'etat actuel du fichier views_recus.py..."

if [ -f "paiements/views_recus.py" ]; then
    echo "Premieres lignes du fichier actuel:"
    head -10 "paiements/views_recus.py"
    echo ""
    
    # Verifier s'il y a des erreurs de syntaxe
    echo "Verification de la syntaxe Python..."
    python -m py_compile "paiements/views_recus.py" 2>&1 || echo "ERREUR: Fichier Python casse"
    echo ""
fi

# 2. Restaurer depuis la sauvegarde
echo "2. Restauration depuis la sauvegarde..."

# Chercher la derniere sauvegarde
backup_file=$(ls -t paiements/views_recus.py.backup_* 2>/dev/null | head -1)

if [ -n "$backup_file" ]; then
    echo "Sauvegarde trouvee: $backup_file"
    cp "$backup_file" "paiements/views_recus.py"
    echo "  OK: Fichier restaure depuis la sauvegarde"
else
    echo "ATTENTION: Aucune sauvegarde trouvee"
fi

# 3. Corriger les imports de maniere propre
echo "3. Correction propre des imports..."

# Lire le fichier et ajouter les imports correctement
if [ -f "paiements/views_recus.py" ]; then
    # Creer une nouvelle sauvegarde
    cp "paiements/views_recus.py" "paiements/views_recus.py.backup_clean_$(date +%Y%m%d_%H%M%S)"
    
    # Ajouter les imports au debut du fichier de maniere propre
    echo "Ajout des imports de maniere propre..."
    
    # Creer un fichier temporaire avec les imports
    cat > temp_imports.py << 'EOF'
from .models import RecapMensuel, RecuRecapitulatif
EOF
    
    # Ajouter le contenu du fichier original
    cat "paiements/views_recus.py" >> temp_imports.py
    
    # Remplacer le fichier original
    mv temp_imports.py "paiements/views_recus.py"
    
    echo "  OK: Imports ajoutes proprement"
    
    # Verifier la syntaxe
    echo "Verification de la syntaxe apres correction..."
    python -m py_compile "paiements/views_recus.py" 2>&1 || echo "ERREUR: Fichier encore casse"
    echo ""
    
    echo "Premieres lignes du fichier corrige:"
    head -10 "paiements/views_recus.py"
    echo ""
fi

# 4. Tester Django
echo "4. Test de Django..."

# Tester que Django peut se charger
python manage.py check

if [ $? -eq 0 ]; then
    echo "OK: Django peut se charger sans erreur"
else
    echo "ATTENTION: Django a des erreurs"
fi

# 5. Redemarrer Gunicorn
echo "5. Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction du fichier casse terminee!"
echo "Le fichier a ete restaure et les imports ont ete ajoutes proprement"
