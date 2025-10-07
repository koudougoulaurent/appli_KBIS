#!/bin/bash

# Script d'urgence pour diagnostiquer et corriger le problème grave
echo "🚨 DIAGNOSTIC D'URGENCE - Application Django plantée"
echo "=================================================="

cd /var/www/kbis_immobilier

# 1. Vérifier l'état de Gunicorn
echo "1. Vérification de l'état de Gunicorn..."
sudo systemctl status gunicorn --no-pager

# 2. Vérifier les logs d'erreur
echo ""
echo "2. Vérification des logs d'erreur Gunicorn..."
sudo journalctl -u gunicorn --no-pager -n 20

# 3. Vérifier les logs d'erreur Django
echo ""
echo "3. Vérification des logs d'erreur Django..."
if [ -f "/var/log/gunicorn/error.log" ]; then
    echo "=== Dernières erreurs Gunicorn ==="
    tail -20 /var/log/gunicorn/error.log
else
    echo "Fichier de log Gunicorn non trouvé"
fi

# 4. Tester Django directement
echo ""
echo "4. Test de Django directement..."
python manage.py check 2>&1

# 5. Vérifier la syntaxe Python des fichiers modifiés
echo ""
echo "5. Vérification de la syntaxe Python..."
echo "Test de paiements/views_recus.py..."
python -m py_compile "paiements/views_recus.py" 2>&1 || echo "❌ ERREUR: Syntaxe Python invalide dans views_recus.py"

echo "Test de paiements/models.py..."
python -m py_compile "paiements/models.py" 2>&1 || echo "❌ ERREUR: Syntaxe Python invalide dans models.py"

# 6. Vérifier les imports
echo ""
echo "6. Vérification des imports..."
echo "=== Imports dans paiements/views_recus.py ==="
grep -n "from .models import" "paiements/views_recus.py" || echo "❌ Aucun import trouvé"

# 7. Restaurer depuis la dernière sauvegarde valide
echo ""
echo "7. Restauration depuis la dernière sauvegarde valide..."

# Chercher la dernière sauvegarde
backup_file=$(ls -t paiements/views_recus.py.backup_* 2>/dev/null | head -1)

if [ -n "$backup_file" ]; then
    echo "Sauvegarde trouvée: $backup_file"
    cp "$backup_file" "paiements/views_recus.py"
    echo "✅ Fichier restauré depuis la sauvegarde"
else
    echo "❌ Aucune sauvegarde trouvée"
fi

# 8. Corriger manuellement l'import
echo ""
echo "8. Correction manuelle de l'import..."

# Vérifier l'état actuel
echo "État actuel du fichier:"
head -25 "paiements/views_recus.py" | grep -n "from .models import"

# Décommenter l'import si nécessaire
sed -i 's/# from \.models import RecapMensuel, RecuRecapitulatif/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"

echo "Import corrigé"

# 9. Tester Django après correction
echo ""
echo "9. Test de Django après correction..."
python manage.py check 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Django peut se charger sans erreur"
else
    echo "❌ Django a encore des erreurs"
fi

# 10. Redémarrer Gunicorn
echo ""
echo "10. Redémarrage de Gunicorn..."
sudo systemctl stop gunicorn
sleep 2
sudo systemctl start gunicorn
sleep 3

# Vérifier le statut
echo "Vérification du statut après redémarrage..."
sudo systemctl status gunicorn --no-pager

# 11. Test final
echo ""
echo "11. Test final de l'application..."
curl -I http://localhost:8000/ 2>/dev/null || echo "❌ Application non accessible"

echo ""
echo "🔧 DIAGNOSTIC TERMINÉ"
echo "Si l'application ne fonctionne toujours pas, il faut vérifier les logs détaillés."
