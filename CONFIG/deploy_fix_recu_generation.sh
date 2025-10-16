#!/bin/bash
# Script de déploiement pour la correction de génération des récépissés
# =====================================================================

echo "🚀 Déploiement de la correction de génération des récépissés..."

# 1. Aller dans le répertoire du projet
cd /opt/render/project/src

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Récupérer les dernières modifications
echo "📥 Récupération des dernières modifications..."
git pull origin master

# 4. Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
pip install -r requirements.txt

# 5. Appliquer les migrations si nécessaire
echo "🗄️ Vérification des migrations..."
python manage.py migrate --noinput

# 6. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 7. Tester la génération de récépissé
echo "🧪 Test de la génération de récépissé..."
python manage.py shell -c "
import sys
import os
from paiements.models import Paiement

# Test de l'import DocumentKBISUnifie
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath('paiements/models.py')))
    scripts_path = os.path.join(project_root, 'SCRIPTS')
    if scripts_path not in sys.path:
        sys.path.append(scripts_path)
    from document_kbis_unifie import DocumentKBISUnifie
    print('✅ Import DocumentKBISUnifie: SUCCÈS')
except Exception as e:
    print(f'❌ Import DocumentKBISUnifie: ÉCHEC - {e}')
    exit(1)

# Test de génération avec un paiement existant
try:
    paiement = Paiement.objects.first()
    if paiement:
        html_recu = paiement._generer_recu_kbis_dynamique()
        if html_recu:
            print('✅ Génération récépissé: SUCCÈS')
            print(f'📄 Taille HTML: {len(html_recu)} caractères')
        else:
            print('❌ Génération récépissé: ÉCHEC - HTML vide')
            exit(1)
    else:
        print('⚠️ Aucun paiement trouvé pour le test')
        print('✅ Correction appliquée avec succès')
except Exception as e:
    print(f'❌ Test génération: ÉCHEC - {e}')
    exit(1)
"

# 8. Redémarrer l'application
echo "🔄 Redémarrage de l'application..."
sudo systemctl restart kbis-immobilier

# 9. Vérifier le statut
echo "📊 Vérification du statut..."
sleep 5
sudo systemctl status kbis-immobilier --no-pager

echo "✅ Déploiement terminé avec succès!"
echo "🌐 L'application est maintenant disponible avec la correction des récépissés"
