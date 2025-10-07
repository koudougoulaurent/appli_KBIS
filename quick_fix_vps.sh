#!/bin/bash

# Script de correction rapide pour le VPS
echo "=== Correction rapide du VPS ==="

# 1. Sauvegarder
echo "1. Sauvegarde..."
ssh root@78.138.58.185 "cd /var/www/kbis_immobilier && cp paiements/models.py paiements/models.py.backup_$(date +%Y%m%d_%H%M%S)"

# 2. Copier le fichier models.py
echo "2. Copie du fichier models.py..."
scp paiements/models.py root@78.138.58.185:/var/www/kbis_immobilier/paiements/models.py

# 3. Corriger views_recus.py
echo "3. Correction de views_recus.py..."
ssh root@78.138.58.185 "cd /var/www/kbis_immobilier && sed -i 's/from \\.models import RecapMensuel, RecuRecapitulatif/from .models import RecapMensuel, RecuRecapitulatif/' paiements/views_recus.py"

# 4. Nettoyer les marqueurs Git
echo "4. Nettoyage des marqueurs Git..."
ssh root@78.138.58.185 "cd /var/www/kbis_immobilier && sed -i '/<<<<<<< Updated upstream/d; /=======/d; />>>>>>> Stashed changes/d' paiements/views_recus.py"

# 5. Vérifier et redémarrer
echo "5. Vérification et redémarrage..."
ssh root@78.138.58.185 "cd /var/www/kbis_immobilier && source venv/bin/activate && python manage.py check && sudo systemctl restart gunicorn && sudo systemctl restart nginx"

echo "=== Correction terminée ==="
echo "Testez: https://78.138.58.185/paiements/recus-recapitulatifs/creer/1/"
