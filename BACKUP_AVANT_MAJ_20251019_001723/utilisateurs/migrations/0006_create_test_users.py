from django.db import migrations
from django.contrib.auth import get_user_model
from django.db import transaction

def create_test_users(apps, schema_editor):
    """Crée les utilisateurs de test lors de la migration."""
    User = get_user_model()
    GroupeTravail = apps.get_model('utilisateurs', 'GroupeTravail')
    
    try:
        with transaction.atomic():
            # Créer les groupes de travail s'ils n'existent pas
            groupes_data = [
                {
                    'nom': 'PRIVILEGE',
                    'description': 'Groupe avec tous les privilèges',
                    'permissions': {
                        'modules': ['all'],
                        'actions': ['create', 'read', 'update', 'delete']
                    }
                },
                {
                    'nom': 'ADMINISTRATION',
                    'description': 'Groupe d\'administration',
                    'permissions': {
                        'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                        'actions': ['create', 'read', 'update']
                    }
                },
                {
                    'nom': 'CAISSE',
                    'description': 'Groupe de gestion de la caisse',
                    'permissions': {
                        'modules': ['paiements', 'contrats'],
                        'actions': ['create', 'read', 'update']
                    }
                },
                {
                    'nom': 'CONTROLES',
                    'description': 'Groupe de contrôles',
                    'permissions': {
                        'modules': ['proprietes', 'contrats'],
                        'actions': ['read', 'update']
                    }
                }
            ]
            
            groupes = {}
            for group_data in groupes_data:
                groupe, created = GroupeTravail.objects.get_or_create(
                    nom=group_data['nom'],
                    defaults={
                        'description': group_data['description'],
                        'permissions': group_data['permissions'],
                        'actif': True
                    }
                )
                groupes[group_data['nom']] = groupe
            
            # Créer les utilisateurs de test
            users_data = [
                {
                    'username': 'admin',
                    'email': 'admin@test.com',
                    'first_name': 'Admin',
                    'last_name': 'Test',
                    'password': 'admin123',
                    'groupe_nom': 'PRIVILEGE',
                    'is_staff': True,
                    'is_superuser': True,
                    'telephone': '+226 70 00 00 01',
                    'poste': 'Administrateur Principal',
                    'departement': 'Direction'
                },
                {
                    'username': 'caisse',
                    'email': 'caisse@test.com',
                    'first_name': 'Marie',
                    'last_name': 'Caisse',
                    'password': 'caisse123',
                    'groupe_nom': 'CAISSE',
                    'is_staff': True,
                    'is_superuser': False,
                    'telephone': '+226 70 00 00 02',
                    'poste': 'Agent de Caisse',
                    'departement': 'Finances'
                },
                {
                    'username': 'admin_immobilier',
                    'email': 'admin.immobilier@test.com',
                    'first_name': 'Jean',
                    'last_name': 'Immobilier',
                    'password': 'admin123',
                    'groupe_nom': 'ADMINISTRATION',
                    'is_staff': True,
                    'is_superuser': False,
                    'telephone': '+226 70 00 00 03',
                    'poste': 'Administrateur Immobilier',
                    'departement': 'Immobilier'
                },
                {
                    'username': 'controleur',
                    'email': 'controleur@test.com',
                    'first_name': 'Sophie',
                    'last_name': 'Controleur',
                    'password': 'controle123',
                    'groupe_nom': 'CONTROLES',
                    'is_staff': True,
                    'is_superuser': False,
                    'telephone': '+226 70 00 00 04',
                    'poste': 'Contrôleur',
                    'departement': 'Contrôle'
                },
                {
                    'username': 'test',
                    'email': 'test@test.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'password': 'test123',
                    'groupe_nom': 'CAISSE',
                    'is_staff': False,
                    'is_superuser': False,
                    'telephone': '+226 70 00 00 05',
                    'poste': 'Utilisateur Test',
                    'departement': 'Test'
                }
            ]
            
            for user_data in users_data:
                groupe_nom = user_data.pop('groupe_nom')
                
                # Vérifier si l'utilisateur existe déjà
                if not User.objects.filter(username=user_data['username']).exists():
                    # Récupérer le groupe
                    groupe = groupes.get(groupe_nom)
                    if groupe:
                        # Créer l'utilisateur
                        user = User.objects.create_user(
                            **user_data
                        )
                        user.groupe_travail = groupe
                        user.save()
                        print(f"✅ Utilisateur {user.username} créé (Groupe: {groupe.nom})")
                    else:
                        print(f"❌ Groupe {groupe_nom} non trouvé pour {user_data['username']}")
                else:
                    print(f"ℹ️  Utilisateur {user_data['username']} existe déjà")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la création des utilisateurs de test: {e}")
        import traceback
        traceback.print_exc()

def reverse_create_test_users(apps, schema_editor):
    """Supprime les utilisateurs de test lors du rollback."""
    User = get_user_model()
    
    test_usernames = ['admin', 'caisse', 'admin_immobilier', 'controleur', 'test']
    User.objects.filter(username__in=test_usernames).delete()
    print("🗑️  Utilisateurs de test supprimés")

class Migration(migrations.Migration):
    dependencies = [
        ('utilisateurs', '0005_alter_utilisateur_telephone'),
    ]

    operations = [
        migrations.RunPython(create_test_users, reverse_create_test_users),
    ]
