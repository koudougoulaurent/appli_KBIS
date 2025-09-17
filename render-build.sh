#!/usr/bin/env bash
# Render build script for Django application

echo "🚀 Starting Render build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser and test users (always recreate for SQLite)
echo "👤 Creating users for SQLite database..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from proprietes.models import TypeBien
from core.models import ConfigurationEntreprise

User = get_user_model()

# Create groups
groups = ['ADMINISTRATION', 'PRIVILEGE', 'CAISSE', 'CONTROLES']
for group_name in groups:
    group, created = Group.objects.get_or_create(name=group_name)
    print(f"✅ Groupe: {group_name}")

# Create superuser (force update for SQLite)
try:
    admin = User.objects.get(username='admin')
    admin.delete()
    print("🗑️ Ancien admin supprimé")
except User.DoesNotExist:
    pass

admin = User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='admin123'
)
admin.is_superuser = True
admin.is_staff = True
admin.save()
print("✅ Superuser 'admin' créé")

# Add admin to ADMINISTRATION group
admin_group = Group.objects.get(name='ADMINISTRATION')
admin.groups.add(admin_group)

# Create test users (force recreation for SQLite)
test_users = [
    {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groups': ['CAISSE']},
    {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groups': ['CONTROLES']},
    {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groups': ['ADMINISTRATION']},
    {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groups': ['PRIVILEGE']},
]

for user_data in test_users:
    # Delete existing user if exists
    try:
        existing_user = User.objects.get(username=user_data['username'])
        existing_user.delete()
        print(f"🗑️ Ancien utilisateur {user_data['username']} supprimé")
    except User.DoesNotExist:
        pass
    
    # Create new user
    user = User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password']
    )
    user.is_staff = True
    user.save()
    
    # Add to groups
    for group_name in user_data['groups']:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
    
    print(f"✅ Utilisateur: {user_data['username']} créé")

# Create property types
types_bien = [
    'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
    'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce',
    'Entrepôt', 'Garage', 'Terrain', 'Autre'
]

for type_name in types_bien:
    type_bien, created = TypeBien.objects.get_or_create(nom=type_name)
    if created:
        print(f"✅ Type créé: {type_name}")

# Create company configuration
config, created = ConfigurationEntreprise.objects.get_or_create(
    nom_entreprise="Gestion Immobilière KBIS",
    defaults={
        'adresse': "123 Rue de l'Immobilier",
        'ville': "Ouagadougou",
        'code_postal': "01 BP 1234",
        'telephone': "+226 25 12 34 56",
        'email': "contact@kbis.bf"
    }
)
if created:
    print("✅ Configuration entreprise créée")
else:
    print("✅ Configuration entreprise existante")

print("🎉 Tous les utilisateurs et données créés avec succès !")
EOF

echo "✅ Build process completed successfully!"
