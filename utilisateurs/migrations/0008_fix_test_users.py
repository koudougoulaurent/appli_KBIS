from django.db import migrations
from django.contrib.auth import get_user_model
from django.db import transaction

def fix_test_users(apps, schema_editor):
    """Corrige la création des utilisateurs de test."""
    User = get_user_model()
    GroupeTravail = apps.get_model('utilisateurs', 'GroupeTravail')
    
    try:
        with transaction.atomic():
            # Supprimer les utilisateurs existants s'ils existent
            test_usernames = ['admin', 'caisse', 'admin_immobilier', 'controleur', 'test']
            User.objects.filter(username__in=test_usernames).delete()
            print("🗑️  Anciens utilisateurs de test supprimés")
            
            # Récupérer les groupes existants
            groupes = {}
            for groupe in GroupeTravail.objects.all():
                groupes[groupe.nom] = groupe
            
            # Créer les utilisateurs de test (sans les champs problématiques)
            users_data = [
                {
                    'username': 'admin',
                    'email': 'admin@test.com',
                    'first_name': 'Admin',
                    'last_name': 'Test',
                    'password': 'admin123',
                    'groupe_nom': 'PRIVILEGE',
                    'is_staff': True,
                    'is_superuser': True
                },
                {
                    'username': 'caisse',
                    'email': 'caisse@test.com',
                    'first_name': 'Marie',
                    'last_name': 'Caisse',
                    'password': 'caisse123',
                    'groupe_nom': 'CAISSE',
                    'is_staff': True,
                    'is_superuser': False
                },
                {
                    'username': 'admin_immobilier',
                    'email': 'admin.immobilier@test.com',
                    'first_name': 'Jean',
                    'last_name': 'Immobilier',
                    'password': 'admin123',
                    'groupe_nom': 'ADMINISTRATION',
                    'is_staff': True,
                    'is_superuser': False
                },
                {
                    'username': 'controleur',
                    'email': 'controleur@test.com',
                    'first_name': 'Sophie',
                    'last_name': 'Controleur',
                    'password': 'controle123',
                    'groupe_nom': 'CONTROLES',
                    'is_staff': True,
                    'is_superuser': False
                },
                {
                    'username': 'test',
                    'email': 'test@test.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'password': 'test123',
                    'groupe_nom': 'CAISSE',
                    'is_staff': False,
                    'is_superuser': False
                }
            ]
            
            for user_data in users_data:
                groupe_nom = user_data.pop('groupe_nom')
                
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
                    
            print("🎉 Tous les utilisateurs de test ont été créés avec succès!")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la création des utilisateurs de test: {e}")
        import traceback
        traceback.print_exc()

def reverse_fix_test_users(apps, schema_editor):
    """Supprime les utilisateurs de test lors du rollback."""
    User = get_user_model()
    
    test_usernames = ['admin', 'caisse', 'admin_immobilier', 'controleur', 'test']
    User.objects.filter(username__in=test_usernames).delete()
    print("🗑️  Utilisateurs de test supprimés")

class Migration(migrations.Migration):
    dependencies = [
        ('utilisateurs', '0007_force_create_test_users'),
    ]

    operations = [
        migrations.RunPython(fix_test_users, reverse_fix_test_users),
    ]
