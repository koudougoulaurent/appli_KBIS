#!/bin/bash

# Script final complet pour corriger tous les problemes sur le VPS
echo "Correction finale complete des problemes sur le VPS..."

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

# 3. Nettoyer les modeles dupliques et corriger les relations
echo "3. Nettoyage des modeles dupliques et correction des relations..."

# Creer un script Python pour nettoyer les modeles
cat > fix_models_cleanup.py << 'EOF'
#!/usr/bin/env python3
import re

def fix_models():
    # Lire le fichier models.py
    with open('paiements/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creer une sauvegarde
    with open('paiements/models.py.backup_cleanup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Supprimer toutes les classes RecuRecapitulatif dupliquees
    # Garder seulement la premiere occurrence
    lines = content.split('\n')
    new_lines = []
    in_recu_class = False
    recu_class_count = 0
    
    for line in lines:
        if 'class RecuRecapitulatif(models.Model):' in line:
            recu_class_count += 1
            if recu_class_count == 1:
                # Garder la premiere occurrence
                in_recu_class = True
                new_lines.append(line)
            else:
                # Ignorer les occurrences suivantes
                in_recu_class = False
        elif in_recu_class and line.strip() == '' and len(new_lines) > 0:
            # Fin de la classe
            new_lines.append(line)
            in_recu_class = False
        elif in_recu_class:
            new_lines.append(line)
        elif not in_recu_class:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    # Corriger la relation OneToOneField en ForeignKey
    new_content = new_content.replace(
        'recapitulatif = models.OneToOneField(\n        RecapMensuel,\n        on_delete=models.CASCADE,\n        related_name=\'recu\',\n        verbose_name=_("Récapitulatif")\n    )',
        'recapitulatif = models.ForeignKey(\n        RecapMensuel,\n        on_delete=models.CASCADE,\n        related_name=\'recus\',\n        verbose_name=_("Récapitulatif")\n    )'
    )
    
    # Sauvegarder le fichier modifie
    with open('paiements/models.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"OK: {recu_class_count} classes RecuRecapitulatif trouvees, 1 gardee")
    print("OK: Relation OneToOneField remplacee par ForeignKey")

if __name__ == '__main__':
    fix_models()
EOF

# Executer le script de nettoyage
python fix_models_cleanup.py

# Supprimer le script temporaire
rm fix_models_cleanup.py

echo "Correction terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Correction finale complete terminee avec succes!"
