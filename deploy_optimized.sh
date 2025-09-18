#!/bin/bash
# Script de déploiement optimisé pour Render

echo "🚀 Déploiement optimisé de l'application de gestion immobilière"

# Variables d'environnement
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
export PYTHONPATH=/opt/render/project/src

# Installation des dépendances optimisées
echo "📦 Installation des dépendances..."
pip install -r requirements_production.txt

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=gestion_immobiliere.settings_production

# Migrations de base de données
echo "🗄️ Application des migrations..."
python manage.py migrate --settings=gestion_immobiliere.settings_production

# Création du superutilisateur si nécessaire
echo "👤 Création du superutilisateur..."
python manage.py shell --settings=gestion_immobiliere.settings_production << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superutilisateur créé")
else:
    print("Superutilisateur existe déjà")
EOF

# Optimisation de la base de données
echo "⚡ Optimisation de la base de données..."
python manage.py shell --settings=gestion_immobiliere.settings_production << EOF
from django.db import connection
cursor = connection.cursor()
# Création d'index pour optimiser les requêtes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_propriete_bailleur ON proprietes_propriete(bailleur_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_propriete_type ON proprietes_propriete(type_bien_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_propriete_disponible ON proprietes_propriete(disponible);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_contrat_propriete ON contrats_contrat(propriete_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_paiement_contrat ON paiements_paiement(contrat_id);")
print("Index créés")
EOF

# Test de l'application
echo "🧪 Test de l'application..."
python manage.py check --settings=gestion_immobiliere.settings_production

echo "✅ Déploiement terminé avec succès!"
echo "🌐 Application disponible sur: https://votre-app.onrender.com"
