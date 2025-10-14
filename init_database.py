#!/usr/bin/env python
"""
Script pour initialiser la base de données sur Render
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def init_database():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données...")
    
    try:
        # Supprimer le fichier de base de données s'il existe
        import os
        db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
        if os.path.exists(db_path):
            print("🗑️ Suppression de l'ancienne base de données...")
            os.remove(db_path)
        
        # Utiliser --run-syncdb pour créer les tables directement
        print("🚀 Création des tables avec --run-syncdb...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        
        # Créer un superutilisateur par défaut
        print("👤 Création du superutilisateur...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@kbis.com',
                password='admin123'
            )
            print("✅ Superutilisateur créé: admin/admin123")
        else:
            print("ℹ️ Superutilisateur existe déjà")
        
        print("✅ Base de données initialisée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == '__main__':
    init_database()
