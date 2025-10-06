#!/bin/bash

# Script pour diagnostiquer et corriger les modèles manquants
echo "🔍 DIAGNOSTIC DES MODÈLES MANQUANTS"
echo "=================================="

cd /var/www/kbis_immobilier

# 1. Vérifier quels modèles existent dans paiements/models.py
echo "1. Vérification des modèles dans paiements/models.py..."
echo "=== Modèles définis dans paiements/models.py ==="
grep -n "class.*models.Model" "paiements/models.py" | head -10

# 2. Chercher spécifiquement RecapMensuel et RecuRecapitulatif
echo ""
echo "2. Recherche des modèles RecapMensuel et RecuRecapitulatif..."
grep -n "class RecapMensuel\|class RecuRecapitulatif" "paiements/models.py" || echo "❌ Modèles non trouvés"

# 3. Vérifier les imports dans views_recus.py
echo ""
echo "3. Vérification des imports dans views_recus.py..."
grep -n "from .models import" "paiements/views_recus.py"

# 4. Tester Django avec plus de détails
echo ""
echo "4. Test de Django avec détails..."
python manage.py check --verbosity=2 2>&1

# 5. Tester l'import spécifique
echo ""
echo "5. Test de l'import spécifique..."
python -c "
try:
    from paiements.models import RecapMensuel, RecuRecapitulatif
    print('✅ Import réussi: RecapMensuel et RecuRecapitulatif')
except ImportError as e:
    print(f'❌ Erreur d\'import: {e}')
except Exception as e:
    print(f'❌ Autre erreur: {e}')
"

# 6. Vérifier si les modèles existent dans d'autres fichiers
echo ""
echo "6. Recherche des modèles dans d'autres fichiers..."
find . -name "*.py" -exec grep -l "class RecapMensuel\|class RecuRecapitulatif" {} \;

# 7. Si les modèles n'existent pas, les commenter temporairement
echo ""
echo "7. Correction temporaire - commenter les imports problématiques..."

# Créer une sauvegarde
cp "paiements/views_recus.py" "paiements/views_recus.py.backup_before_comment_$(date +%Y%m%d_%H%M%S)"

# Commenter les imports problématiques
sed -i 's/from \.models import RecapMensuel, RecuRecapitulatif/# from .models import RecapMensuel, RecuRecapitulatif  # Temporairement commenté/' "paiements/views_recus.py"

echo "Imports commentés temporairement"

# 8. Tester Django après correction
echo ""
echo "8. Test de Django après correction..."
python manage.py check 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Django peut se charger sans erreur"
else
    echo "❌ Django a encore des erreurs"
fi

# 9. Redémarrer Gunicorn
echo ""
echo "9. Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# 10. Test final
echo ""
echo "10. Test final de l'application..."
curl -I http://localhost:8000/ 2>/dev/null || echo "❌ Application non accessible"

echo ""
echo "🔧 DIAGNOSTIC TERMINÉ"
echo "Si l'application fonctionne maintenant, le problème était les modèles manquants."
echo "Il faudra ajouter les modèles RecapMensuel et RecuRecapitulatif dans paiements/models.py"
