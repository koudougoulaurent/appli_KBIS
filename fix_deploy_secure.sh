#!/bin/bash
# Script de correction pour /opt/deploy_secure.sh
# Usage: ./fix_deploy_secure.sh

echo "🔧 Correction du script /opt/deploy_secure.sh"
echo "============================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./fix_deploy_secure.sh"
    exit 1
fi

# Vérifier que le script existe
if [ ! -f "/opt/deploy_secure.sh" ]; then
    echo "❌ Le script /opt/deploy_secure.sh n'existe pas"
    exit 1
fi

echo "✅ Script original trouvé"

# Créer une sauvegarde
echo "📦 Création d'une sauvegarde..."
cp /opt/deploy_secure.sh /opt/deploy_secure.sh.broken.$(date +%Y%m%d_%H%M%S)
echo "✅ Sauvegarde créée"

# Restaurer depuis la sauvegarde si elle existe
if [ -f "/opt/deploy_secure.sh.backup.$(date +%Y%m%d)*" ]; then
    echo "🔄 Restauration depuis la sauvegarde..."
    ls -la /opt/deploy_secure.sh.backup.* | tail -1 | awk '{print $9}' | xargs -I {} cp {} /opt/deploy_secure.sh
    chmod +x /opt/deploy_secure.sh
    echo "✅ Script restauré depuis la sauvegarde"
else
    echo "❌ Aucune sauvegarde trouvée"
    echo "   Le script original doit être restauré manuellement"
    exit 1
fi

echo ""
echo "✅ Correction terminée !"
echo ""
echo "🔍 Vérification du script..."
if bash -n /opt/deploy_secure.sh; then
    echo "✅ Syntaxe du script corrigée"
else
    echo "❌ Le script a encore des erreurs de syntaxe"
    echo "   Veuillez vérifier manuellement"
fi

echo ""
echo "🚀 Vous pouvez maintenant utiliser :"
echo "   sudo /opt/deploy_secure.sh"
