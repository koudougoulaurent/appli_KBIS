#!/bin/bash

# Script simple pour corriger les imports manquants
echo "Correction simple des imports manquants..."

cd /var/www/kbis_immobilier

# 1. Créer une sauvegarde
echo "1. Création d'une sauvegarde..."
cp "paiements/views_recus.py" "paiements/views_recus.py.backup_$(date +%Y%m%d_%H%M%S)"
echo "Sauvegarde créée"

# 2. Corriger l'import commenté dans paiements/views_recus.py
echo "2. Correction de l'import commenté..."

# Décommenter l'import
sed -i 's/# from \.models import RecapMensuel, RecuRecapitulatif  # Modèles supprimés, RecapMensuel/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"

echo "Import décommenté dans paiements/views_recus.py"

# 3. Vérifier la correction
echo "3. Vérification de la correction..."
echo "=== Import dans paiements/views_recus.py ==="
grep -n "from .models import" "paiements/views_recus.py"

# 4. Tester la syntaxe Python
echo "4. Test de la syntaxe Python..."
python -m py_compile "paiements/views_recus.py" 2>&1 || echo "ERREUR: Syntaxe Python invalide"

# 5. Tester Django
echo "5. Test de Django..."
python manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Django peut se charger sans erreur"
else
    echo "❌ Django a des erreurs"
fi

# 6. Redémarrer Gunicorn
echo "6. Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# 7. Test final
echo "7. Test final..."
curl -I http://localhost:8000/paiements/recus-recapitulatifs/creer/1/ 2>/dev/null || echo "Erreur de connexion"

echo ""
echo "✅ Correction terminée !"
