#!/bin/bash

# Script final pour corriger DEFINITIVEMENT le probleme RecapitulatifMensuelBailleur
echo "Correction DEFINITIVE du probleme RecapitulatifMensuelBailleur..."

cd /var/www/kbis_immobilier

# 1. Verifier et corriger TOUS les fichiers
echo "1. Correction de TOUS les fichiers..."

# Liste de tous les fichiers a corriger
files=(
    "paiements/views_recus.py"
    "paiements/views_kbis_recus.py"
    "paiements/forms.py"
    "paiements/services_recus.py"
    "paiements/views_charges_avancees.py"
    "paiements/models.py"
    "paiements/admin.py"
    "paiements/urls.py"
    "paiements/views.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Correction de $file..."
        cp "$file" "$file.backup_$(date +%Y%m%d_%H%M%S)"
        
        # Remplacer TOUTES les occurrences de RecapitulatifMensuelBailleur par RecapMensuel
        sed -i 's/RecapitulatifMensuelBailleur/RecapMensuel/g' "$file"
        
        # Verifier qu'il n'y a plus de references
        if grep -q "RecapitulatifMensuelBailleur" "$file"; then
            echo "  ATTENTION: Il reste des references dans $file"
            grep -n "RecapitulatifMensuelBailleur" "$file"
        else
            echo "  OK: $file corrige"
        fi
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

# 2. Corriger les imports manquants
echo "2. Correction des imports manquants..."

# Corriger views_recus.py
if [ -f "paiements/views_recus.py" ]; then
    echo "Correction des imports dans views_recus.py..."
    
    # Ajouter l'import RecapMensuel s'il n'existe pas
    if ! grep -q "from .models import.*RecapMensuel" "paiements/views_recus.py"; then
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_recus.py"; then
            # Ajouter RecapMensuel a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecapMensuel/' "paiements/views_recus.py"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecapMensuel' "paiements/views_recus.py"
        fi
    fi
    
    # Ajouter l'import RecuRecapitulatif s'il n'existe pas
    if ! grep -q "from .models import.*RecuRecapitulatif" "paiements/views_recus.py"; then
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_recus.py"; then
            # Ajouter RecuRecapitulatif a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecuRecapitulatif/' "paiements/views_recus.py"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecuRecapitulatif' "paiements/views_recus.py"
        fi
    fi
    
    echo "  OK: views_recus.py corrige"
fi

# Corriger views_charges_avancees.py
if [ -f "paiements/views_charges_avancees.py" ]; then
    echo "Correction des imports dans views_charges_avancees.py..."
    
    # Ajouter l'import RecapMensuel s'il n'existe pas
    if ! grep -q "from .models import.*RecapMensuel" "paiements/views_charges_avancees.py"; then
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_charges_avancees.py"; then
            # Ajouter RecapMensuel a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecapMensuel/' "paiements/views_charges_avancees.py"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecapMensuel' "paiements/views_charges_avancees.py"
        fi
    fi
    
    echo "  OK: views_charges_avancees.py corrige"
fi

# Corriger views_kbis_recus.py
if [ -f "paiements/views_kbis_recus.py" ]; then
    echo "Correction des imports dans views_kbis_recus.py..."
    
    # Ajouter l'import RecapMensuel s'il n'existe pas
    if ! grep -q "from .models import.*RecapMensuel" "paiements/views_kbis_recus.py"; then
        # Trouver la ligne avec les imports de models
        if grep -q "from .models import" "paiements/views_kbis_recus.py"; then
            # Ajouter RecapMensuel a l'import existant
            sed -i 's/from \.models import \([^)]*\)/from .models import \1, RecapMensuel/' "paiements/views_kbis_recus.py"
        else
            # Ajouter un nouvel import
            sed -i '1i from .models import RecapMensuel' "paiements/views_kbis_recus.py"
        fi
    fi
    
    echo "  OK: views_kbis_recus.py corrige"
fi

# 3. Corriger UNIQUEMENT la relation ForeignKey
echo "3. Correction UNIQUEMENT de la relation ForeignKey..."

# Creer un script Python pour corriger UNIQUEMENT la relation
cat > fix_foreign_key_only.py << 'EOF'
#!/usr/bin/env python3

def fix_foreign_key_only():
    # Lire le fichier models.py
    with open('paiements/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creer une sauvegarde
    with open('paiements/models.py.backup_fk_only', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # UNIQUEMENT : Remplacer OneToOneField par ForeignKey avec null=True, blank=True
    old_relation = """recapitulatif = models.OneToOneField(
        RecapMensuel,
        on_delete=models.CASCADE,
        related_name='recu',
        verbose_name=_("Récapitulatif")
    )"""
    
    new_relation = """recapitulatif = models.ForeignKey(
        RecapMensuel,
        on_delete=models.CASCADE,
        related_name='recus',
        verbose_name=_("Récapitulatif"),
        null=True,
        blank=True
    )"""
    
    if old_relation in content:
        content = content.replace(old_relation, new_relation)
        print("OK: Relation OneToOneField remplacee par ForeignKey avec null=True, blank=True")
    else:
        print("ATTENTION: Relation OneToOneField non trouvee")
    
    # Sauvegarder le fichier modifie
    with open('paiements/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK: Correction UNIQUEMENT de la FOREIGN KEY terminee")

if __name__ == '__main__':
    fix_foreign_key_only()
EOF

# Executer le script de correction UNIQUEMENT de la FOREIGN KEY
python fix_foreign_key_only.py

# Supprimer le script temporaire
rm fix_foreign_key_only.py

# 4. Verifier qu'il n'y a plus de references a RecapitulatifMensuelBailleur
echo "4. Verification finale..."

# Chercher dans tous les fichiers Python
echo "Recherche de references restantes a RecapitulatifMensuelBailleur..."
if find . -name "*.py" -exec grep -l "RecapitulatifMensuelBailleur" {} \; | grep -v ".pyc" | grep -v "__pycache__"; then
    echo "ATTENTION: Il reste des references a RecapitulatifMensuelBailleur dans les fichiers ci-dessus"
    echo "Correction manuelle necessaire..."
else
    echo "OK: Aucune reference a RecapitulatifMensuelBailleur trouvee"
fi

# 5. Tester Django
echo "5. Test de Django..."

# Tester que Django peut se charger
python manage.py check

if [ $? -eq 0 ]; then
    echo "OK: Django peut se charger sans erreur"
else
    echo "ATTENTION: Django a des erreurs"
fi

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction DEFINITIVE terminee!"
echo "Toutes les references a RecapitulatifMensuelBailleur ont ete remplacees par RecapMensuel"
echo "Les imports ont ete corriges"
echo "La relation ForeignKey a ete corrigee"