from django.db import migrations
from django.core.management import call_command

def create_test_users(apps, schema_editor):
    """Crée les utilisateurs de test lors de la migration."""
    try:
        call_command('create_test_users')
    except Exception as e:
        print(f"Erreur lors de la création des utilisateurs de test: {e}")

def reverse_create_test_users(apps, schema_editor):
    """Supprime les utilisateurs de test lors du rollback."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    test_usernames = ['admin', 'caisse', 'admin_immobilier', 'controleur', 'test']
    User.objects.filter(username__in=test_usernames).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('utilisateurs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_test_users, reverse_create_test_users),
    ]
