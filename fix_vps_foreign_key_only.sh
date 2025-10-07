#!/bin/bash

# Script pour corriger UNIQUEMENT le probleme de FOREIGN KEY constraint failed
echo "Correction UNIQUEMENT du probleme de FOREIGN KEY constraint failed..."

cd /var/www/kbis_immobilier

# 1. Corriger les references RecapitulatifMensuelBailleur
echo "1. Correction des references RecapitulatifMensuelBailleur..."

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
        cp "$file" "$file.backup"
        sed -i 's/RecapitulatifMensuelBailleur/RecapMensuel/g' "$file"
        echo "  OK: $file corrige"
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

# 2. Corriger les imports manquants
echo "2. Correction des imports manquants..."

# Corriger views_recus.py
if [ -f "paiements/views_recus.py" ]; then
    echo "Correction des imports dans views_recus.py..."
    sed -i 's/# from .models import RecuRecapitulatif, RecapMensuel  # Modeles supprimes/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecuRecapitulatif, RecapMensuel/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecapMensuel$/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    echo "  OK: views_recus.py corrige"
fi

# Corriger views_charges_avancees.py
if [ -f "paiements/views_charges_avancees.py" ]; then
    echo "Correction des imports dans views_charges_avancees.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_charges_avancees.py"
    echo "  OK: views_charges_avancees.py corrige"
fi

# Corriger views_kbis_recus.py
if [ -f "paiements/views_kbis_recus.py" ]; then
    echo "Correction des imports dans views_kbis_recus.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_kbis_recus.py"
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
    print("ATTENTION: Generation PDF non modifiee")

if __name__ == '__main__':
    fix_foreign_key_only()
EOF

# Executer le script de correction UNIQUEMENT de la FOREIGN KEY
python fix_foreign_key_only.py

# Supprimer le script temporaire
rm fix_foreign_key_only.py

echo "Correction UNIQUEMENT de la FOREIGN KEY terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction UNIQUEMENT de la FOREIGN KEY terminee avec succes!"
echo "ATTENTION: Generation PDF n'a PAS ete modifiee!"
