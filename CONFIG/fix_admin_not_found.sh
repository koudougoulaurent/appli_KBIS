#!/bin/bash
# Script pour corriger le problème "Admin Not Found" après redéploiement
# =====================================================================

echo "🔧 Correction du problème Admin Not Found..."

# 1. Aller dans le répertoire du projet
cd /opt/render/project/src

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Récupérer les dernières modifications
echo "📥 Récupération des dernières modifications..."
git pull origin master

# 4. Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# 5. Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py migrate --noinput

# 6. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 7. Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Création d\\'un superutilisateur...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

# 8. Vérifier la configuration
echo "🔍 Vérification de la configuration..."
python manage.py shell -c "
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
print(f'STATIC_ROOT: {settings.STATIC_ROOT}')
print(f'ROOT_URLCONF: {settings.ROOT_URLCONF}')
"

# 9. Tester l'admin
echo "🧪 Test de l'admin Django..."
python manage.py shell -c "
from django.contrib.admin.sites import site
from django.urls import reverse
try:
    admin_url = reverse('admin:index')
    print(f'✅ URL Admin: {admin_url}')
    print('✅ Configuration admin OK')
except Exception as e:
    print(f'❌ Erreur admin: {e}')
"

# 10. Redémarrer l'application
echo "🔄 Redémarrage de l'application..."
sudo systemctl restart kbis-immobilier

# 11. Attendre et vérifier le statut
echo "⏳ Attente du redémarrage..."
sleep 10

echo "📊 Vérification du statut..."
sudo systemctl status kbis-immobilier --no-pager

echo "✅ Correction terminée!"
echo "🌐 Testez maintenant: https://appli-kbis-3.onrender.com/admin/"
