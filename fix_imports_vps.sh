#!/bin/bash

# Script pour corriger SPECIFIQUEMENT les imports manquants
echo "Correction SPECIFIQUE des imports manquants..."

cd /var/www/kbis_immobilier

# 1. Verifier le fichier views_recus.py
echo "1. Verification du fichier views_recus.py..."

if [ -f "paiements/views_recus.py" ]; then
    echo "Contenu actuel des imports dans views_recus.py:"
    head -20 "paiements/views_recus.py" | grep -E "(import|from)"
    echo ""
    
    # Verifier si RecapMensuel est importe
    if ! grep -q "RecapMensuel" "paiements/views_recus.py"; then
        echo "ATTENTION: RecapMensuel n'est pas importe dans views_recus.py"
        
        # Ajouter l'import RecapMensuel
        echo "Ajout de l'import RecapMensuel..."
        
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_recus.py"; then
            # Ajouter RecapMensuel a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecapMensuel/' "paiements/views_recus.py"
            echo "  OK: RecapMensuel ajoute a l'import existant"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecapMensuel' "paiements/views_recus.py"
            echo "  OK: Nouvel import RecapMensuel ajoute"
        fi
    else
        echo "OK: RecapMensuel est deja importe"
    fi
    
    # Verifier si RecuRecapitulatif est importe
    if ! grep -q "RecuRecapitulatif" "paiements/views_recus.py"; then
        echo "ATTENTION: RecuRecapitulatif n'est pas importe dans views_recus.py"
        
        # Ajouter l'import RecuRecapitulatif
        echo "Ajout de l'import RecuRecapitulatif..."
        
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_recus.py"; then
            # Ajouter RecuRecapitulatif a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecuRecapitulatif/' "paiements/views_recus.py"
            echo "  OK: RecuRecapitulatif ajoute a l'import existant"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecuRecapitulatif' "paiements/views_recus.py"
            echo "  OK: Nouvel import RecuRecapitulatif ajoute"
        fi
    else
        echo "OK: RecuRecapitulatif est deja importe"
    fi
    
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
        
        # Verifier si RecapMensuel est importe
        if ! grep -q "RecapMensuel" "$file"; then
            echo "  ATTENTION: RecapMensuel n'est pas importe dans $file"
            
            # Ajouter l'import RecapMensuel
            if grep -q "from .models import" "$file"; then
                sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecapMensuel/' "$file"
                echo "  OK: RecapMensuel ajoute a l'import existant dans $file"
            else
                sed -i '1i from .models import RecapMensuel' "$file"
                echo "  OK: Nouvel import RecapMensuel ajoute dans $file"
            fi
        else
            echo "  OK: RecapMensuel est deja importe dans $file"
        fi
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

echo "Correction des imports terminee!"
echo "Les imports RecapMensuel et RecuRecapitulatif ont ete ajoutes"
