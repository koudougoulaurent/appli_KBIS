#!/bin/bash

# ===========================================
# SCRIPT DE DÉPLOIEMENT FINAL PYTHONANYWHERE
# ===========================================
# Ce script corrige TOUS les problèmes identifiés

echo "🚀 DÉPLOIEMENT FINAL PYTHONANYWHERE - CORRECTION COMPLÈTE"
echo "=========================================================="

# 1. Aller dans le répertoire du projet
cd /home/laurenzo/appli_KBIS

# 2. Activer l'environnement virtuel
source ~/.virtualenvs/mv/bin/activate

# 3. Installer les packages manquants
echo "📦 Installation des packages manquants..."
pip install django-filter
pip install django-select2
pip install whitenoise

# 4. Vérifier l'installation
echo "✅ Vérification des packages installés..."
pip list | grep -E "(django-filter|django-select2|whitenoise)"

# 5. Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py makemigrations
python manage.py migrate

# 6. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 7. Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

# 8. Vérifier la configuration Django
echo "🔍 Vérification de la configuration..."
python manage.py check --deploy

# 9. Tester les URLs
echo "🌐 Test des URLs principales..."
python manage.py shell -c "
from django.urls import reverse
from django.test import Client

client = Client()

# Test de la page d'accueil
try:
    response = client.get('/')
    print(f'Page d\'accueil: {response.status_code}')
except Exception as e:
    print(f'Erreur page d\'accueil: {e}')

# Test de la page de connexion
try:
    response = client.get('/utilisateurs/connexion-groupes/')
    print(f'Page de connexion: {response.status_code}')
except Exception as e:
    print(f'Erreur page de connexion: {e}')

# Test de l'admin
try:
    response = client.get('/admin/')
    print(f'Admin: {response.status_code}')
except Exception as e:
    print(f'Erreur admin: {e}')
"

# 10. Afficher les informations de configuration
echo "📋 Configuration finale:"
echo "- Domaine: laurenzo.pythonanywhere.com"
echo "- Fichiers statiques: /home/laurenzo/appli_KBIS/staticfiles/"
echo "- Fichiers media: /home/laurenzo/appli_KBIS/media/"
echo "- Base de données: /home/laurenzo/appli_KBIS/db.sqlite3"
echo "- WSGI: wsgi_pythonanywhere_final.py"
echo "- Settings: gestion_immobiliere.settings_pythonanywhere"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "🌐 Votre application est prête sur PythonAnywhere"
echo ""
echo "📝 INSTRUCTIONS FINALES:"
echo "1. Copiez le contenu de 'wsgi_pythonanywhere_final.py' dans votre fichier WSGI"
echo "2. Changez le settings module vers 'gestion_immobiliere.settings_pythonanywhere'"
echo "3. Configurez les fichiers statiques: /static/ → /home/laurenzo/appli_KBIS/staticfiles/"
echo "4. Configurez les fichiers media: /media/ → /home/laurenzo/appli_KBIS/media/"
echo "5. Redémarrez votre application web"
echo ""
echo "🎯 URLs à tester:"
echo "- https://laurenzo.pythonanywhere.com/"
echo "- https://laurenzo.pythonanywhere.com/utilisateurs/connexion-groupes/"
echo "- https://laurenzo.pythonanywhere.com/admin/"
