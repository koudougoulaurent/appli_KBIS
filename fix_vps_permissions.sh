#!/bin/bash

# Script pour corriger les permissions sur le VPS
# Résout l'erreur 'str' object has no attribute 'get'

echo "🚀 Correction des permissions sur le VPS..."

# Aller dans le répertoire de l'application
cd /var/www/kbis_immobilier

# Activer l'environnement virtuel
source venv/bin/activate

# Arrêter les services temporairement
echo "⏸️  Arrêt des services..."
sudo systemctl stop kbis-immobilier
sudo systemctl stop nginx

# Exécuter le script de correction
echo "🔧 Exécution du script de correction..."
python fix_permissions_data.py

# Redémarrer les services
echo "▶️  Redémarrage des services..."
sudo systemctl start kbis-immobilier
sudo systemctl start nginx

# Vérifier le statut
echo "✅ Vérification du statut..."
sudo systemctl status kbis-immobilier --no-pager -l
sudo systemctl status nginx --no-pager -l

echo "🎉 Correction terminée !"
echo "🌐 Testez maintenant : https://78.138.58.185/utilisateurs/dashboard/PRIVILEGE/"

