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

# Create superuser
admin, created = User.objects.get_or_create(username='admin')
if created:
    admin.set_password('admin123')
    admin.email = 'admin@example.com'
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
    print("✅ Superuser 'admin' créé")
else:
    admin.set_password('admin123')
    admin.save()
    print("✅ Superuser 'admin' mis à jour")

# Add admin to ADMINISTRATION group
admin_group = Group.objects.get(name='ADMINISTRATION')
admin.groups.add(admin_group)

# Create test users
test_users = [
    {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groups': ['CAISSE']},
    {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groups': ['CONTROLES']},
    {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groups': ['ADMINISTRATION']},
    {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groups': ['PRIVILEGE']},
]

for user_data in test_users:
    user, created = User.objects.get_or_create(username=user_data['username'])
    user.set_password(user_data['password'])
    user.email = user_data['email']
    user.is_staff = True
    user.save()
    
    # Add to groups
    for group_name in user_data['groups']:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
    
    print(f"✅ Utilisateur: {user_data['username']}")

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
