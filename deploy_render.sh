#!/bin/bash
# Script de déploiement pour Render.com - KBIS INTERNATIONAL

echo "🚀 DÉPLOIEMENT KBIS INTERNATIONAL SUR RENDER"
echo "=============================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements_render.txt

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=gestion_immobiliere.settings_render

# Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py migrate --settings=gestion_immobiliere.settings_render

# Créer un superutilisateur (optionnel)
echo "👤 Création du superutilisateur..."
python manage.py shell --settings=gestion_immobiliere.settings_render << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@kbis.com', 'admin123')
    print("Superutilisateur créé: admin/admin123")
else:
    print("Superutilisateur existe déjà")
EOF

# Vérifier la configuration
echo "🔍 Vérification de la configuration..."
python manage.py check --settings=gestion_immobiliere.settings_render

echo "✅ Déploiement terminé avec succès !"
echo "🌐 Votre application est disponible sur Render"
