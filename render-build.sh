#!/usr/bin/env bash
# Script de build ultra-simple pour Render

echo "🚀 Demarrage du build sur Render..."

# Installer Django et les dependances essentielles
echo "📦 Installation des dependances essentielles..."
pip install Django==4.2.7
pip install psycopg[binary]==3.1.18
pip install dj-database-url==2.1.0
pip install gunicorn==21.2.0
pip install whitenoise==6.6.0
pip install Pillow==10.4.0
pip install reportlab==4.0.7
pip install openpyxl==3.1.2
pip install python-dateutil==2.8.2
pip install django-crispy-forms==2.1
pip install crispy-bootstrap5==0.7
pip install djangorestframework==3.14.0
pip install django-filter==23.5
pip install django-autocomplete-light==3.9.1
pip install django-select2==8.1.0
pip install django-extensions==3.2.3

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate

# Creer la configuration d'entreprise
echo "🏢 Configuration de l'entreprise..."
python manage.py shell -c "
from core.models import ConfigurationEntreprise
ConfigurationEntreprise.objects.all().delete()
config = ConfigurationEntreprise.objects.create(
    nom_entreprise='KBIS IMMOBILIER',
    adresse='123 Rue de l\\'Immobilier',
    ville='Ouagadougou',
    code_postal='01 BP 1234',
    telephone='+226 25 12 34 56',
    email='contact@kbis.bf',
    actif=True
)
print('✅ Configuration entreprise creee!')
"

# Creer les utilisateurs de test
echo "👥 Creation des utilisateurs de test..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
User = get_user_model()

# Supprimer les utilisateurs existants
User.objects.filter(username__in=['admin', 'gestionnaire', 'agent', 'comptable', 'demo']).delete()

# Creer les utilisateurs
admin = User.objects.create_user('admin', 'admin@kbis.bf', 'admin123', first_name='Admin', last_name='System', is_staff=True, is_superuser=True)
gestionnaire = User.objects.create_user('gestionnaire', 'gestionnaire@kbis.bf', 'gestion123', first_name='Jean', last_name='Gestionnaire', is_staff=True)
agent = User.objects.create_user('agent', 'agent@kbis.bf', 'agent123', first_name='Marie', last_name='Agent')
comptable = User.objects.create_user('comptable', 'comptable@kbis.bf', 'comptable123', first_name='Paul', last_name='Comptable')
demo = User.objects.create_user('demo', 'demo@kbis.bf', 'demo123', first_name='Demo', last_name='User')

# Creer les groupes
admin_group, _ = Group.objects.get_or_create(name='ADMINISTRATION')
privilege_group, _ = Group.objects.get_or_create(name='PRIVILEGE')
caisse_group, _ = Group.objects.get_or_create(name='CAISSE')
controle_group, _ = Group.objects.get_or_create(name='CONTROLE')

# Assigner les groupes
admin.groups.add(admin_group, privilege_group)
gestionnaire.groups.add(admin_group)
agent.groups.add(privilege_group)
comptable.groups.add(caisse_group)
demo.groups.add(controle_group)

print('✅ Utilisateurs de test crees!')
"

echo "🎉 Build termine avec succes!"
